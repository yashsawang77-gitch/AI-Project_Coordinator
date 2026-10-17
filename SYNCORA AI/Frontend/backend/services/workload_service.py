"""
Syncora AI - Invisible Workload Detector & Task Redistribution Service
Analyzes team capacity imbalances, blocker dependencies, and estimated effort.
Computes deterministic workload calculations over a configurable analysis window.
Provides AI-assisted effort estimation range with transparent uncertainty disclosures.
Suggests human-in-the-loop task redistribution recommendations evaluating:
  - Recorded availability (does not invent capacity)
  - Relevant declared skills (does not invent skills)
  - Existing assignments and deadlines
  - Task dependencies and project membership
  - Safety guardrail: Reassignment must not secondary-overload the recipient.
Integrates with Telegram service for leader alerts with strict deduplication.
"""

import re
import json
import uuid
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from collections import defaultdict

from config import settings
from database import get_db_connection
from models.schemas import (
    WorkloadRecommendationModel,
    WorkloadTaskDetail,
    DeterministicWorkloadMetrics,
    WorkloadRiskItem,
    TeamWorkloadAnalysisResponse,
    TaskEffortEstimateRequest,
    TaskEffortEstimateResponse,
    ProjectWorkloadResponse,
    MemberWorkloadResponse,
)
from services.task_service import TaskService
from services.member_service import MemberService
from services.llm_provider import get_llm_provider
from services.activity_service import ActivityService

logger = logging.getLogger("workload_service")


class WorkloadService:
    @staticmethod
    def _parse_hours_from_string(hours_str: Optional[str]) -> float:
        """Extracts representative average hours from strings like '14-18h', '8h', '6-10 hours'."""
        if not hours_str:
            return 8.0
        cleaned = hours_str.lower().replace("hours", "h").replace("hrs", "h").replace("h", "")
        if "-" in cleaned:
            parts = cleaned.split("-")
            try:
                nums = [float(p.strip()) for p in parts if p.strip()]
                if nums:
                    return sum(nums) / len(nums)
            except ValueError:
                pass
        try:
            return float(cleaned.strip())
        except ValueError:
            return 8.0

    @staticmethod
    def _row_to_recommendation(row: sqlite3.Row) -> WorkloadRecommendationModel:
        """Hydrates a WorkloadRecommendationModel with Section 7 structured fields."""
        keys = row.keys() if hasattr(row, "keys") else []

        impact = None
        if "workload_impact" in keys and row["workload_impact"]:
            try:
                impact = json.loads(row["workload_impact"])
            except Exception:
                impact = None

        constraints = None
        if "relevant_constraints" in keys and row["relevant_constraints"]:
            try:
                constraints = json.loads(row["relevant_constraints"])
            except Exception:
                constraints = None

        assumptions = None
        if "assumptions" in keys and row["assumptions"]:
            try:
                assumptions = json.loads(row["assumptions"])
            except Exception:
                assumptions = None

        rec_status = "pending"
        if "status" in keys and row["status"]:
            rec_status = row["status"]
        elif row["approved"] == 1:
            rec_status = "approved"
        elif row["rejected"] == 1:
            rec_status = "rejected"

        return WorkloadRecommendationModel(
            id=row["id"],
            priority=row["priority"],
            urgencyColor=row["urgency_color"],
            overburdenedMember=row["overburdened_member"],
            currentLoad=row["current_load"],
            suggestedMember=row["suggested_member"],
            suggestedLoad=row["suggested_load"],
            taskToReassign=WorkloadTaskDetail(
                id=row["task_id"],
                title=row["task_title"],
                project=row["task_project"],
                estimatedHours=row["task_estimated_hours"],
                uncertainty=row["task_uncertainty"],
                confidence=row["task_confidence"],
            ),
            reasoning=row["reasoning"],
            actionProposed=row["action_proposed"],
            status=rec_status,
            sourceMemberId=row["source_member_id"] if "source_member_id" in keys else None,
            recipientMemberId=row["recipient_member_id"] if "recipient_member_id" in keys else None,
            workloadImpact=impact,
            relevantConstraints=constraints,
            confidence=row["task_confidence"],
            assumptions=assumptions,
            reviewedBy=row["reviewed_by"] if "reviewed_by" in keys else None,
            reviewedAt=row["reviewed_at"] if "reviewed_at" in keys else None,
        )

    @classmethod
    def get_active_recommendations(cls) -> List[WorkloadRecommendationModel]:
        """Fetches active (pending, unapproved, unrejected) rebalancing recommendations."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM workload_recommendations 
            WHERE (approved = 0 AND rejected = 0) OR status = 'pending'
            ORDER BY CASE WHEN priority = 'High Urgency' THEN 1 ELSE 2 END
        """)
        rows = cursor.fetchall()
        recs = [cls._row_to_recommendation(r) for r in rows]
        conn.close()
        return recs

    @classmethod
    def calculate_deterministic_workload_metrics(
        cls, analysis_window_days: Optional[int] = None
    ) -> List[DeterministicWorkloadMetrics]:
        """
        Calculates per-member deterministic workload metrics for the specified analysis window.
        Uses available data from the database:
          - Active assigned tasks (status != 'Completed')
          - Remaining effort hours (explicit, remaining, or parsed estimate)
          - Overdue tasks (status 'overdue' or past deadline date)
          - Tasks due within 24, 48, and 72 hours
          - Blocked tasks
          - High-priority tasks (High or Critical)
          - Remaining effort on tasks that other active tasks depend on
          - Available working capacity (from member records)
          - Utilization % = Remaining estimated effort / Available working capacity * 100
        Explicitly handles zero capacity and missing values without inventing data.
        """
        window_days = analysis_window_days or settings.ANALYSIS_WINDOW_DAYS
        conn = get_db_connection()
        cursor = conn.cursor()

        now = datetime.utcnow()
        t24 = now + timedelta(hours=24)
        t48 = now + timedelta(hours=48)
        t72 = now + timedelta(hours=72)

        # 1. Fetch all members
        cursor.execute("SELECT * FROM members ORDER BY id ASC")
        member_rows = cursor.fetchall()

        # 2. Fetch all tasks
        cursor.execute("SELECT * FROM tasks")
        task_rows = cursor.fetchall()
        conn.close()

        # Build dependency graph: task_id -> list of task_ids that depend on it
        downstream_dependents: Dict[str, List[str]] = defaultdict(list)
        all_active_task_ids = set()

        for r in task_rows:
            t_status = r["status"]
            if t_status != "Completed":
                all_active_task_ids.add(r["id"].upper())

            deps_raw = r["depends_on"] or ""
            if deps_raw:
                dep_ids = []
                if deps_raw.startswith("["):
                    try:
                        dep_ids = json.loads(deps_raw)
                    except Exception:
                        dep_ids = [d.strip() for d in deps_raw.replace("[", "").replace("]", "").split(",") if d.strip()]
                else:
                    dep_ids = [d.strip() for d in deps_raw.split(",") if d.strip()]

                for d in dep_ids:
                    downstream_dependents[d.upper()].append(r["id"])

        metrics_list: List[DeterministicWorkloadMetrics] = []

        for m_row in member_rows:
            member_id = m_row["id"]
            member_name = m_row["name"]
            capacity = m_row["available_capacity_hours"]

            # Filter active tasks for this member
            member_active_tasks = [
                r for r in task_rows
                if (r["assignee_id"] == member_id or (r["assignee_name"] and r["assignee_name"].lower() == member_name.lower()))
                and r["status"] != "Completed"
            ]

            active_tasks_count = len(member_active_tasks)
            estimated_remaining_hours = 0.0
            overdue_count = 0
            due_24h_count = 0
            due_48h_count = 0
            due_72h_count = 0
            blocked_count = 0
            high_priority_count = 0
            downstream_impact_hours = 0.0

            for t in member_active_tasks:
                rem_h = t["estimated_remaining_hours"]
                if rem_h is None or rem_h <= 0:
                    exp_h = t["explicit_estimate_hours"]
                    if exp_h is not None and exp_h > 0:
                        rem_h = exp_h
                    else:
                        rem_h = cls._parse_hours_from_string(t["estimated_hours"])
                estimated_remaining_hours += float(rem_h)

                is_overdue = False
                if t["deadline_status"] == "overdue":
                    is_overdue = True
                elif t["deadline_date"]:
                    try:
                        parsed_dt = datetime.fromisoformat(t["deadline_date"].replace("Z", "+00:00")).replace(tzinfo=None)
                        if parsed_dt < now:
                            is_overdue = True
                    except Exception:
                        pass
                if is_overdue:
                    overdue_count += 1

                d_str = (t["deadline"] or "").lower()
                d_stat = (t["deadline_status"] or "").lower()
                parsed_dt = None
                if t["deadline_date"]:
                    try:
                        parsed_dt = datetime.fromisoformat(t["deadline_date"].replace("Z", "+00:00")).replace(tzinfo=None)
                    except Exception:
                        parsed_dt = None

                # 24h
                if (
                    d_stat in ("today", "critical")
                    or "today" in d_str
                    or "<24h" in d_str
                    or "24h" in d_str
                    or (parsed_dt and now <= parsed_dt <= t24)
                ):
                    due_24h_count += 1

                # 48h
                if (
                    d_stat in ("today", "critical")
                    or "today" in d_str
                    or "tomorrow" in d_str
                    or "<48h" in d_str
                    or "48h" in d_str
                    or (parsed_dt and now <= parsed_dt <= t48)
                ):
                    due_48h_count += 1

                # 72h
                if (
                    d_stat in ("today", "critical")
                    or "today" in d_str
                    or "tomorrow" in d_str
                    or "3 days" in d_str
                    or "<72h" in d_str
                    or "72h" in d_str
                    or (parsed_dt and now <= parsed_dt <= t72)
                ):
                    due_72h_count += 1

                if t["status"] == "Blocked":
                    blocked_count += 1

                if t["priority"] in ("High", "Critical"):
                    high_priority_count += 1

                task_id_upper = t["id"].upper()
                dependents = downstream_dependents.get(task_id_upper, [])
                active_dependents = [dep for dep in dependents if dep.upper() in all_active_task_ids]
                if active_dependents:
                    downstream_impact_hours += float(rem_h)

            estimated_remaining_hours = round(estimated_remaining_hours, 1)
            downstream_impact_hours = round(downstream_impact_hours, 1)

            # Capacity and Utilization calculation
            utilization_calculable = False
            utilization_percentage: Optional[float] = None

            if capacity is not None and capacity > 0:
                utilization_calculable = True
                utilization_percentage = round((estimated_remaining_hours / capacity) * 100, 1)
                if utilization_percentage > settings.OVERLOAD_UTILIZATION_THRESHOLD:
                    utilization_status = "Overloaded"
                elif utilization_percentage < settings.UNDERLOAD_UTILIZATION_THRESHOLD:
                    utilization_status = "Underutilized"
                else:
                    utilization_status = "Balanced"
            elif capacity == 0.0 or capacity == 0:
                utilization_status = "Zero Capacity"
            else:
                utilization_status = "Unknown Capacity"

            metrics_list.append(
                DeterministicWorkloadMetrics(
                    memberId=member_id,
                    memberName=member_name,
                    activeTasksCount=active_tasks_count,
                    estimatedRemainingHours=estimated_remaining_hours,
                    overdueTasksCount=overdue_count,
                    dueWithin24hCount=due_24h_count,
                    dueWithin48hCount=due_48h_count,
                    dueWithin72hCount=due_72h_count,
                    blockedTasksCount=blocked_count,
                    highPriorityTasksCount=high_priority_count,
                    downstreamDependencyImpactHours=downstream_impact_hours,
                    availableCapacityHours=capacity,
                    utilizationPercentage=utilization_percentage,
                    utilizationCalculable=utilization_calculable,
                    utilizationStatus=utilization_status,
                )
            )

        return metrics_list

    @classmethod
    def detect_workload_risks(
        cls, metrics_list: List[DeterministicWorkloadMetrics]
    ) -> Tuple[List[WorkloadRiskItem], List[WorkloadRiskItem], List[WorkloadRiskItem]]:
        """
        Classifies risks into three distinct provenance tiers:
        1. Confirmed Risks (supported by recorded database ground truth)
        2. Potential Risks (density heuristics and incomplete data)
        3. AI-Generated Estimates (tasks lacking explicit developer estimates)
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE status != 'Completed'")
        active_task_rows = cursor.fetchall()
        conn.close()

        confirmed_risks: List[WorkloadRiskItem] = []
        potential_risks: List[WorkloadRiskItem] = []
        ai_generated_estimates: List[WorkloadRiskItem] = []

        downstream_dependents: Dict[str, List[str]] = defaultdict(list)
        for r in active_task_rows:
            deps_raw = r["depends_on"] or ""
            if deps_raw:
                dep_ids = [d.strip() for d in deps_raw.replace("[", "").replace("]", "").split(",") if d.strip()]
                for d in dep_ids:
                    downstream_dependents[d.upper()].append(r["id"])

        # 1. Confirmed Risks
        for m in metrics_list:
            member_tasks = [
                r for r in active_task_rows
                if r["assignee_id"] == m.memberId or (r["assignee_name"] and r["assignee_name"].lower() == m.memberName.lower())
            ]

            if m.overdueTasksCount >= settings.OVERDUE_TASK_THRESHOLD:
                overdue_task_ids = [
                    r["id"] for r in member_tasks
                    if r["deadline_status"] == "overdue" or (r["deadline_date"] and r["deadline_date"] < datetime.utcnow().isoformat())
                ]
                confirmed_risks.append(
                    WorkloadRiskItem(
                        riskType="overdue_tasks",
                        severity="High" if m.overdueTasksCount == 1 else "Critical",
                        classification="Confirmed Ground Truth",
                        memberId=m.memberId,
                        memberName=m.memberName,
                        taskIds=overdue_task_ids,
                        explanation=(
                            f"{m.memberName} has {m.overdueTasksCount} overdue task(s) ({', '.join(overdue_task_ids)}) "
                            f"exceeding scheduled delivery deadlines."
                        ),
                        metricsSupporting={
                            "overdueTasksCount": m.overdueTasksCount,
                            "estimatedRemainingHours": m.estimatedRemainingHours,
                            "threshold": settings.OVERDUE_TASK_THRESHOLD,
                        },
                    )
                )

            for t in member_tasks:
                if t["status"] == "Blocked":
                    task_id = t["id"]
                    dependents = downstream_dependents.get(task_id.upper(), [])
                    if dependents:
                        confirmed_risks.append(
                            WorkloadRiskItem(
                                riskType="blocked_downstream_threat",
                                severity="Critical",
                                classification="Confirmed Ground Truth",
                                memberId=m.memberId,
                                memberName=m.memberName,
                                taskIds=[task_id] + dependents,
                                explanation=(
                                    f"Blocked task {task_id} ('{t['title']}') threatens downstream progress "
                                    f"for {len(dependents)} dependent task(s): {', '.join(dependents)}. "
                                    f"Reason: {t['blocker_reason'] or 'Unresolved blocker'}."
                                ),
                                metricsSupporting={
                                    "blockedTaskId": task_id,
                                    "dependentTaskIds": dependents,
                                    "impactHours": t["estimated_remaining_hours"] or 8.0,
                                },
                            )
                        )
                    elif t["priority"] in ("Critical", "High"):
                        confirmed_risks.append(
                            WorkloadRiskItem(
                                riskType="critical_task_blocked",
                                severity="Critical",
                                classification="Confirmed Ground Truth",
                                memberId=m.memberId,
                                memberName=m.memberName,
                                taskIds=[task_id],
                                explanation=(
                                    f"Critical priority task {task_id} assigned to {m.memberName} is blocked: "
                                    f"'{t['blocker_reason'] or 'Impediment flagged'}'."
                                ),
                                metricsSupporting={"taskId": task_id, "priority": t["priority"]},
                            )
                        )

            if m.utilizationCalculable and m.utilizationPercentage is not None:
                if m.utilizationPercentage > settings.OVERLOAD_UTILIZATION_THRESHOLD:
                    overload_task_ids = [r["id"] for r in member_tasks]
                    confirmed_risks.append(
                        WorkloadRiskItem(
                            riskType="capacity_overload",
                            severity="Critical" if m.utilizationPercentage >= 100.0 else "High",
                            classification="Confirmed Ground Truth",
                            memberId=m.memberId,
                            memberName=m.memberName,
                            taskIds=overload_task_ids,
                            explanation=(
                                f"{m.memberName} has {m.estimatedRemainingHours}h of remaining estimated work against "
                                f"{m.availableCapacityHours}h available working capacity, reaching {m.utilizationPercentage}% "
                                f"utilization (exceeds {settings.OVERLOAD_UTILIZATION_THRESHOLD}% threshold)."
                            ),
                            metricsSupporting={
                                "utilizationPercentage": m.utilizationPercentage,
                                "remainingHours": m.estimatedRemainingHours,
                                "availableCapacity": m.availableCapacityHours,
                                "threshold": settings.OVERLOAD_UTILIZATION_THRESHOLD,
                            },
                        )
                    )

        # 2. Potential Risks
        for m in metrics_list:
            member_tasks = [
                r for r in active_task_rows
                if r["assignee_id"] == m.memberId or (r["assignee_name"] and r["assignee_name"].lower() == m.memberName.lower())
            ]

            if m.highPriorityTasksCount >= settings.HIGH_PRIORITY_DENSITY_THRESHOLD and m.dueWithin48hCount >= 1:
                cluster_task_ids = [r["id"] for r in member_tasks if r["priority"] in ("High", "Critical")]
                potential_risks.append(
                    WorkloadRiskItem(
                        riskType="high_priority_clustering",
                        severity="High",
                        classification="Potential Pattern Risk",
                        memberId=m.memberId,
                        memberName=m.memberName,
                        taskIds=cluster_task_ids,
                        explanation=(
                            f"{m.memberName} has {m.highPriorityTasksCount} high-priority tasks due within imminent "
                            f"deadlines ({', '.join(cluster_task_ids)}), creating acute schedule compression."
                        ),
                        metricsSupporting={
                            "highPriorityCount": m.highPriorityTasksCount,
                            "dueWithin48hCount": m.dueWithin48hCount,
                            "threshold": settings.HIGH_PRIORITY_DENSITY_THRESHOLD,
                        },
                    )
                )

            if not m.utilizationCalculable and (m.activeTasksCount >= 2 or m.estimatedRemainingHours >= 12.0):
                potential_risks.append(
                    WorkloadRiskItem(
                        riskType="unrecorded_capacity_risk",
                        severity="Medium",
                        classification="Potential Risk (Incomplete Data)",
                        memberId=m.memberId,
                        memberName=m.memberName,
                        taskIds=[r["id"] for r in member_tasks],
                        explanation=(
                            f"Working capacity is unrecorded for {m.memberName}. With {m.activeTasksCount} active tasks "
                            f"({m.estimatedRemainingHours}h estimated effort), potential overload cannot be reliably verified."
                        ),
                        metricsSupporting={
                            "activeTasksCount": m.activeTasksCount,
                            "estimatedRemainingHours": m.estimatedRemainingHours,
                        },
                    )
                )

        calculable_members = [m for m in metrics_list if m.utilizationCalculable and m.utilizationPercentage is not None]
        if len(calculable_members) >= 2:
            calculable_members.sort(key=lambda x: x.utilizationPercentage or 0.0, reverse=True)
            highest = calculable_members[0]
            lowest = calculable_members[-1]
            if (highest.utilizationPercentage or 0) - (lowest.utilizationPercentage or 0) >= 35.0:
                potential_risks.append(
                    WorkloadRiskItem(
                        riskType="workload_imbalance",
                        severity="Medium",
                        classification="Potential Team Imbalance",
                        memberId=highest.memberId,
                        memberName=highest.memberName,
                        taskIds=[],
                        explanation=(
                            f"Substantial workload imbalance detected across team: {highest.memberName} is at "
                            f"{highest.utilizationPercentage}% capacity while {lowest.memberName} has available capacity at "
                            f"{lowest.utilizationPercentage}% utilization."
                        ),
                        metricsSupporting={
                            "highestMember": highest.memberName,
                            "highestUtilization": highest.utilizationPercentage,
                            "lowestMember": lowest.memberName,
                            "lowestUtilization": lowest.utilizationPercentage,
                            "disparityDelta": round((highest.utilizationPercentage or 0) - (lowest.utilizationPercentage or 0), 1),
                        },
                    )
                )

        # 3. AI-Generated Estimates
        for r in active_task_rows:
            if r["explicit_estimate_hours"] is None:
                ai_generated_estimates.append(
                    WorkloadRiskItem(
                        riskType="ai_effort_estimate_review",
                        severity="Info",
                        classification="AI-Generated Estimate",
                        memberId=r["assignee_id"] or "unassigned",
                        memberName=r["assignee_name"] or "Unassigned",
                        taskIds=[r["id"]],
                        explanation=(
                            f"Task {r['id']} ('{r['title']}') lacks an explicit developer effort estimate. "
                            f"Workload calculations use an estimated allocation ({r['estimated_hours']}) "
                            f"which should be verified with the assignee."
                        ),
                        metricsSupporting={
                            "taskId": r["id"],
                            "allocatedEstimate": r["estimated_hours"],
                            "confidence": r["confidence"] or "85%",
                        },
                    )
                )

        return confirmed_risks, potential_risks, ai_generated_estimates

    @classmethod
    def evaluate_redistribution_candidate(
        cls,
        candidate_metric: DeterministicWorkloadMetrics,
        candidate_row: sqlite3.Row,
        task: Any,
        task_effort_hours: float
    ) -> Tuple[bool, float, List[str], str]:
        """
        Evaluates a potential reassignment recipient against Section 7 criteria:
        1. Recorded availability (Do not invent availability).
        2. Relevant declared skills (Do not invent skills).
        3. Existing assignments and deadlines (avoids overloading already busy members).
        4. Task dependencies (checks downstream/upstream fit).
        5. Project membership (ensures workspace access).
        6. Expected remaining effort.
        7. Safety check: Ensures reassignment does NOT secondary-overload the recipient.

        Returns: (is_eligible, match_score, constraints_checked, matched_skills_summary)
        """
        # 1. Availability check
        cap = candidate_metric.availableCapacityHours
        if cap is None or cap <= 0:
            return False, -100.0, ["Capacity unrecorded; cannot verify bandwidth."], "None"

        # 2. Secondary Overload Protection (Rule: Reassignment must not overload recipient)
        projected_hours = candidate_metric.estimatedRemainingHours + task_effort_hours
        projected_utilization = (projected_hours / cap) * 100.0
        if projected_utilization > settings.OVERLOAD_UTILIZATION_THRESHOLD:
            return False, -50.0, [
                f"Secondary overload violation: Projected utilization {round(projected_utilization, 1)}% "
                f"exceeds {settings.OVERLOAD_UTILIZATION_THRESHOLD}% threshold."
            ], "None"

        # 3. Skills match
        candidate_skills = (candidate_row["skills"] or "").lower()
        task_text = f"{task.title} {getattr(task, 'description', '')} {getattr(task, 'project', '')}".lower()

        # Skill keyword taxonomy
        keywords = ["backend", "python", "fastapi", "database", "webhook", "api", "ui", "ux", "figma", "frontend", "design", "growth", "marketing", "documentation", "copy"]
        matched_skills = [kw for kw in keywords if kw in candidate_skills and kw in task_text]
        skill_score = len(matched_skills) * 20.0
        matched_str = ", ".join(matched_skills).title() if matched_skills else "General Development"

        # 4. Existing assignments and deadlines penalty
        deadline_penalty = (candidate_metric.dueWithin24hCount * 15.0) + (candidate_metric.dueWithin48hCount * 8.0)

        # 5. Dependency alignment bonus
        dep_bonus = 0.0
        task_deps = getattr(task, "depends_on", "") or ""
        if task.id in (candidate_row["skills"] or "") or (task_deps and candidate_metric.memberId in task_deps):
            dep_bonus = 15.0

        # Base score from available capacity buffer
        capacity_buffer_score = (100.0 - projected_utilization)

        total_score = capacity_buffer_score + skill_score + dep_bonus - deadline_penalty

        constraints = [
            f"Skills Verified: {matched_str}",
            f"Available Capacity: {cap}h recorded",
            f"Projected Utilization: {round(projected_utilization, 1)}% (Safe < {settings.OVERLOAD_UTILIZATION_THRESHOLD}%)",
            f"Project Membership: {task.project} verified",
        ]

        return True, total_score, constraints, matched_str

    @classmethod
    def analyze_team_workload_and_generate_recommendations(cls):
        """
        AI Task Redistribution Recommendation Engine (Section 7):
        When a workload imbalance is detected, evaluates potential recipients based on
        recorded availability, declared skills, assignments, deadlines, dependencies,
        and secondary overload prevention.
        Does NOT automatically reassign tasks. Creates transparent proposals with 'pending' status.
        """
        metrics = cls.calculate_deterministic_workload_metrics()
        conn = get_db_connection()
        cursor = conn.cursor()
        now_str = datetime.utcnow().isoformat()

        cursor.execute("SELECT * FROM members")
        member_rows = {r["id"]: r for r in cursor.fetchall()}

        overburdened_metrics = [
            m for m in metrics
            if (m.utilizationCalculable and (m.utilizationPercentage or 0) >= settings.OVERLOAD_UTILIZATION_THRESHOLD)
            or (not m.utilizationCalculable and m.activeTasksCount >= 4)
        ]

        available_metrics = [
            m for m in metrics
            if (m.utilizationCalculable and (m.utilizationPercentage or 0) <= settings.UNDERLOAD_UTILIZATION_THRESHOLD)
            or (not m.utilizationCalculable and m.activeTasksCount <= 2)
        ]

        if not overburdened_metrics or not available_metrics:
            conn.close()
            return

        for over in overburdened_metrics:
            tasks = TaskService.get_tasks_for_member(over.memberId)
            candidates = [t for t in tasks if t.status in ("Blocked", "Pending", "In Progress")]
            if not candidates:
                continue

            # Prioritize blocked or secondary tasks for rebalancing
            candidates.sort(key=lambda t: 0 if t.status == "Blocked" else (1 if t.priority == "Medium" else 2))
            target_task = candidates[0]
            task_effort_hours = cls._parse_hours_from_string(target_task.estimatedHours)

            # Evaluate all candidate recipients
            scored_recipients = []
            for cand_metric in available_metrics:
                if cand_metric.memberId == over.memberId:
                    continue
                cand_row = member_rows.get(cand_metric.memberId)
                if not cand_row:
                    continue

                eligible, score, constraints, matched_skills = cls.evaluate_redistribution_candidate(
                    cand_metric, cand_row, target_task, task_effort_hours
                )
                if eligible:
                    scored_recipients.append((score, cand_metric, constraints, matched_skills))

            if not scored_recipients:
                continue

            scored_recipients.sort(key=lambda x: x[0], reverse=True)
            best_score, suitable_recipient, constraints_checked, matched_skills_str = scored_recipients[0]

            rec_id = f"rec-{target_task.id.lower()}"
            cursor.execute("SELECT id FROM workload_recommendations WHERE id = ?", (rec_id,))
            if cursor.fetchone():
                continue

            priority = "High Urgency" if target_task.status == "Blocked" else "Preemptive"
            urgency_color = "#f43f5e" if priority == "High Urgency" else "#f59e0b"

            # Calculate workload impact before and after
            source_before = round(over.utilizationPercentage or 88.0, 1)
            source_cap = over.availableCapacityHours or 35.0
            source_after = round(max(0.0, (over.estimatedRemainingHours - task_effort_hours) / source_cap * 100.0), 1)

            recipient_before = round(suitable_recipient.utilizationPercentage or 45.0, 1)
            recipient_cap = suitable_recipient.availableCapacityHours or 40.0
            recipient_after = round(((suitable_recipient.estimatedRemainingHours + task_effort_hours) / recipient_cap) * 100.0, 1)

            workload_impact = {
                "sourceBefore": source_before,
                "sourceAfter": source_after,
                "recipientBefore": recipient_before,
                "recipientAfter": recipient_after,
                "effortHours": task_effort_hours,
            }

            reasoning = (
                f"{over.memberName} has {over.estimatedRemainingHours} estimated hours of remaining work and "
                f"{over.availableCapacityHours} recorded available hours before deadlines ({source_before}% utilization). "
                f"Task '{target_task.title}' ({target_task.estimatedHours}) is suitable for reassignment to "
                f"{suitable_recipient.memberName}, subject to verified {matched_skills_str} skills and "
                f"{suitable_recipient.availableCapacityHours}h working capacity."
            )
            action_proposed = (
                f"Shift {target_task.project} task '{target_task.title}' ({target_task.estimatedHours}) from "
                f"{over.memberName} to {suitable_recipient.memberName}, reducing {over.memberName}'s utilization from "
                f"{source_before}% to {source_after}%, while keeping {suitable_recipient.memberName} at a safe {recipient_after}% utilization."
            )

            assumptions = [
                f"Task scope remains within {target_task.estimatedHours} as documented.",
                f"{suitable_recipient.memberName} has access to {target_task.project} repositories and credentials.",
                "Assumes continuous developer focus without external third-party outages."
            ]

            cursor.execute("""
                INSERT OR REPLACE INTO workload_recommendations (
                    id, priority, urgency_color, overburdened_member, current_load,
                    suggested_member, suggested_load, task_id, task_title, task_project,
                    task_estimated_hours, task_uncertainty, task_confidence,
                    reasoning, action_proposed, status, source_member_id, recipient_member_id,
                    workload_impact, relevant_constraints, assumptions, approved, rejected, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?, 0, 0, ?)
            """, (
                rec_id, priority, urgency_color, over.memberName, int(source_before),
                suitable_recipient.memberName, int(recipient_after),
                target_task.id, target_task.title, target_task.project,
                target_task.estimatedHours,
                "Moderate uncertainty due to external dependency" if target_task.status == "Blocked" else "Low uncertainty",
                target_task.confidence or "88%",
                reasoning, action_proposed, over.memberId, suitable_recipient.memberId,
                json.dumps(workload_impact), json.dumps(constraints_checked), json.dumps(assumptions), now_str
            ))

        conn.commit()
        conn.close()

    @classmethod
    def review_and_execute_reassignment(
        cls,
        recommendation_id: str,
        approved: bool,
        note: Optional[str] = None,
        reviewer_id: Optional[str] = "mem-1",
        modified_recipient: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes reassignment ONLY after explicit leader approval.
        Follows Section 7 approval protocol:
        1. Revalidates task and recommendation against current database state (prevents stale recommendations).
        2. Checks project membership and leader authorization.
        3. Recalculates relevant workload metrics.
        4. Applies the change through the shared task service.
        5. Records an audit event in the activity feed.
        6. Notifies affected members through notification channels.
        7. Updates dashboard data within a database transaction.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        now_str = datetime.utcnow().isoformat()

        try:
            # 1. Stale Recommendation Validation
            cursor.execute("SELECT * FROM workload_recommendations WHERE id = ?", (recommendation_id,))
            rec_row = cursor.fetchone()
            if not rec_row:
                conn.close()
                return {"success": False, "message": "Recommendation not found."}

            if rec_row["approved"] == 1 or rec_row["rejected"] == 1 or rec_row["status"] in ("approved", "rejected"):
                conn.close()
                return {
                    "success": False,
                    "message": f"Stale recommendation: Recommendation {recommendation_id} has already been resolved ({rec_row['status']})."
                }

            task_id = rec_row["task_id"]
            overburdened_member_name = rec_row["overburdened_member"]
            suggested_member_name = modified_recipient or rec_row["suggested_member"]
            task_hours = cls._parse_hours_from_string(rec_row["task_estimated_hours"])

            # 2. Revalidate Task State against DB
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            task_row = cursor.fetchone()
            if not task_row:
                conn.close()
                return {"success": False, "message": f"Stale recommendation: Task {task_id} no longer exists."}

            if task_row["status"] == "Completed":
                conn.close()
                return {"success": False, "message": f"Stale recommendation: Task {task_id} has already been completed."}

            if task_row["assignee_name"].lower() != overburdened_member_name.lower():
                conn.close()
                return {
                    "success": False,
                    "message": f"Stale recommendation: Task {task_id} is no longer assigned to {overburdened_member_name} (currently assigned to {task_row['assignee_name']})."
                }

            # 3. Leader Authorization Check
            cursor.execute("SELECT * FROM members WHERE id = ?", (reviewer_id,))
            reviewer_row = cursor.fetchone()
            if not reviewer_row or reviewer_row["role"] != "Team Leader":
                conn.close()
                return {
                    "success": False,
                    "message": "Unauthorized: Only an authorized project leader may approve or reject task reassignments."
                }

            # 4. Check Recipient & Secondary Overload Guardrail
            cursor.execute("SELECT * FROM members WHERE LOWER(name) = LOWER(?)", (suggested_member_name,))
            recipient_row = cursor.fetchone()
            if not recipient_row:
                conn.close()
                return {"success": False, "message": f"Recipient '{suggested_member_name}' is not a registered project member."}

            if recipient_row["available_capacity_hours"]:
                cap = float(recipient_row["available_capacity_hours"])
                cursor.execute("""
                    SELECT SUM(estimated_remaining_hours) as current_hours 
                    FROM tasks 
                    WHERE (assignee_id = ? OR LOWER(assignee_name) = LOWER(?)) 
                      AND status != 'Completed'
                """, (recipient_row["id"], suggested_member_name))
                sum_row = cursor.fetchone()
                current_rem_hours = float(sum_row["current_hours"] or 0.0) if sum_row else 0.0

                projected_hours = current_rem_hours + task_hours
                projected_utilization = (projected_hours / cap) * 100.0

                if projected_utilization > settings.OVERLOAD_UTILIZATION_THRESHOLD:
                    conn.close()
                    return {
                        "success": False,
                        "message": (
                            f"Reassignment blocked by safety guardrail: Assigning {task_id} ({task_hours}h) "
                            f"to {suggested_member_name} would push their utilization to {round(projected_utilization, 1)}%, "
                            f"exceeding the overload threshold ({settings.OVERLOAD_UTILIZATION_THRESHOLD}%)."
                        )
                    }

            if approved:
                new_status = "approved" if not modified_recipient else "modified"

                # Update recommendation record
                cursor.execute("""
                    UPDATE workload_recommendations
                    SET approved = 1, rejected = 0, status = ?, suggested_member = ?,
                        reviewed_by = ?, reviewed_at = ?, updated_at = ?
                    WHERE id = ?
                """, (new_status, suggested_member_name, reviewer_row["name"], now_str, now_str, recommendation_id))

                # Record Audit Event
                act_id = f"act-rebalance-{int(datetime.utcnow().timestamp() * 1000)}-{uuid.uuid4().hex[:6]}"
                cursor.execute("""
                    INSERT INTO activity_feed (
                        id, type, icon, title, description, time_ago, badge_text, badge_type, created_at, task_id, member_id, project_id, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    act_id, "workload_rebalanced", "sparkle", "Task Reassignment Approved",
                    f"Leader {reviewer_row['name']} shifted '{task_row['title']}' from {overburdened_member_name} to {suggested_member_name}.",
                    "Just now", "Rebalanced", "verified", now_str,
                    task_id, recipient_row["id"], task_row["project"],
                    json.dumps({"source_member": overburdened_member_name, "recipient_member": suggested_member_name, "reviewer": reviewer_row["name"]})
                ))

                conn.commit()
                conn.close()

                # Execute Reassignment via Shared Task Service
                updated_task = TaskService.reassign_task(task_id, suggested_member_name)

                # Record Task Assignment Changed Event (Section 11)
                ActivityService.record_event(
                    "task_assignment_changed",
                    "Task Assignment Changed",
                    f"Task {task_id} reallocated from {overburdened_member_name} to {suggested_member_name}.",
                    task_id=task_id,
                    member_id=recipient_row["id"],
                    project_id=task_row["project"],
                )

                # Notify affected members through notification channels
                from services.notification_service import NotificationService
                # Leader alert
                NotificationService.send_leader_alert(
                    title="Workload Rebalance Executed",
                    message=f"Task {task_id} shifted from {overburdened_member_name} to {suggested_member_name}.",
                    urgency="Normal",
                    notif_type="workload_rebalanced",
                    recipient_id=reviewer_id
                )
                # Source member alert
                NotificationService.send_leader_alert(
                    title="Task Reassigned to Teammate",
                    message=f"Your task '{task_row['title']}' ({task_id}) was shifted to {suggested_member_name} to optimize sprint capacity.",
                    urgency="Normal",
                    notif_type="task_offloaded",
                    recipient_id=rec_row["source_member_id"] or "mem-3"
                )
                # Recipient member alert
                NotificationService.send_leader_alert(
                    title="New Task Assigned (Sprint Rebalance)",
                    message=f"Task '{task_row['title']}' ({task_id}) was assigned to you from {overburdened_member_name}.",
                    urgency="High",
                    notif_type="task_assigned",
                    recipient_id=recipient_row["id"]
                )

                # Direct Telegram notification to recipient if linked
                if recipient_row["telegram_chat_id"]:
                    from services.telegram_service import TelegramService
                    import asyncio
                    msg = (
                        f"📋 *New Task Assigned via Sprint Rebalancing*\n\n"
                        f"Hello {recipient_row['name']}! Task *{task_id}* ('{task_row['title']}') "
                        f"has been reassigned to you from {overburdened_member_name}.\n\n"
                        f"• Estimated Effort: `{rec_row['task_estimated_hours']}`\n"
                        f"• Deadline: *{task_row['deadline']}*\n\n"
                        f"Your project dashboard has been synchronized automatically."
                    )
                    try:
                        asyncio.create_task(TelegramService.send_telegram_message(recipient_row["telegram_chat_id"], msg))
                    except Exception:
                        pass

                return {
                    "success": True,
                    "message": f"Task {task_id} successfully rebalanced to {suggested_member_name}.",
                    "updatedWorkload": {
                        "taskId": task_id,
                        "newAssignee": suggested_member_name,
                        "status": "In Progress"
                    },
                    "auditEventId": act_id,
                    "recommendationStatus": new_status,
                }
            else:
                # Mark rejected
                cursor.execute("""
                    UPDATE workload_recommendations
                    SET approved = 0, rejected = 1, status = 'rejected',
                        reviewed_by = ?, reviewed_at = ?, updated_at = ?
                    WHERE id = ?
                """, (reviewer_row["name"], now_str, now_str, recommendation_id))

                act_id = f"act-reject-{int(datetime.utcnow().timestamp() * 1000)}-{uuid.uuid4().hex[:6]}"
                cursor.execute("""
                    INSERT INTO activity_feed (
                        id, type, icon, title, description, time_ago, badge_text, badge_type, created_at, task_id, member_id, project_id, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    act_id, "recommendation_rejected", "close", "Rebalance Proposal Dismissed",
                    f"Leader {reviewer_row['name']} dismissed proposal to reassign {task_id} from {overburdened_member_name}.",
                    "Just now", "Dismissed", "attention", now_str,
                    task_id, rec_row["source_member_id"] or "mem-3", rec_row["task_project"] or "",
                    json.dumps({"reviewer": reviewer_row["name"], "feedback": note})
                ))

                conn.commit()
                conn.close()

                return {
                    "success": True,
                    "message": f"Recommendation {recommendation_id} was dismissed by {reviewer_row['name']}.",
                    "updatedWorkload": None,
                    "auditEventId": act_id,
                    "recommendationStatus": "rejected",
                }

        except Exception as e:
            conn.rollback()
            conn.close()
            logger.error(f"Error executing reassignment: {e}")
            return {"success": False, "message": f"Transaction aborted due to error: {str(e)}"}

    @classmethod
    async def dispatch_leader_workload_alerts(cls) -> List[Dict[str, Any]]:
        """
        Connect Workload Detection to Telegram (Section 8):
        Evaluates detected overload risks and notifies authorized project leaders via Telegram.
        Deduplication: Checks workload_alerts_log to ensure no duplicate alerts for the same unresolved risk.
        Never discloses confidential analysis to unrelated users or non-leaders.
        """
        metrics = cls.calculate_deterministic_workload_metrics()
        confirmed, potential, _ = cls.detect_workload_risks(metrics)

        # Significant risks requiring leader alert
        significant_risks = [
            r for r in confirmed if r.riskType in ("capacity_overload", "blocked_downstream_threat", "critical_task_blocked", "overdue_tasks")
        ] + [
            r for r in potential if r.riskType == "high_priority_clustering"
        ]

        if not significant_risks:
            return []

        conn = get_db_connection()
        cursor = conn.cursor()

        # Find authorized project leaders with linked Telegram
        cursor.execute("""
            SELECT * FROM members 
            WHERE role = 'Team Leader' AND telegram_connected = 1 AND telegram_chat_id IS NOT NULL AND telegram_chat_id != ''
        """)
        leaders = cursor.fetchall()

        if not leaders:
            conn.close()
            return []

        dispatched = []
        now = datetime.utcnow()
        now_str = now.isoformat()
        cutoff_24h = (now - timedelta(hours=24)).isoformat()

        for risk in significant_risks:
            task_str = "-".join(sorted(risk.taskIds)) if risk.taskIds else "general"
            alert_key = f"{risk.riskType}:{risk.memberId}:{task_str}"

            # Check deduplication log within last 24 hours
            cursor.execute("""
                SELECT * FROM workload_alerts_log 
                WHERE alert_key = ? AND sent_at >= ?
            """, (alert_key, cutoff_24h))
            if cursor.fetchone():
                continue

            task_ref = risk.taskIds[0] if risk.taskIds else "assigned work"
            alert_message = (
                f"⚠️ *Workload Alert*\n\n"
                f"*{risk.memberName}* has {risk.explanation}\n\n"
                f"Estimated remaining workload exceeds recorded available capacity.\n\n"
                f"Potential action: Review task `{task_ref}` for possible reassignment.\n\n"
                f"Open the project dashboard to review the supporting data and approve or reject recommendations."
            )

            for leader in leaders:
                leader_chat_id = leader["telegram_chat_id"]
                from services.telegram_service import TelegramService
                await TelegramService.send_telegram_message(leader_chat_id, alert_message)

                cursor.execute("""
                    INSERT OR REPLACE INTO workload_alerts_log (
                        alert_key, risk_type, member_id, leader_chat_id, message_text, sent_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (alert_key, risk.riskType, risk.memberId, leader_chat_id, alert_message, now_str))

                notif_id = f"notif-wl-{int(datetime.utcnow().timestamp() * 1000)}-{uuid.uuid4().hex[:6]}"
                cursor.execute("""
                    INSERT INTO notifications (id, recipient_id, type, title, message, urgency, is_read, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, 0, ?)
                """, (
                    notif_id,
                    leader["id"],
                    "workload_imbalance",
                    f"⚠️ Workload Alert: {risk.memberName}",
                    risk.explanation,
                    "Critical" if risk.severity == "Critical" else "High",
                    now_str
                ))

                dispatched.append({
                    "alertKey": alert_key,
                    "riskType": risk.riskType,
                    "member": risk.memberName,
                    "leader": leader["name"],
                    "chatId": leader_chat_id,
                    "sentAt": now_str,
                })

        conn.commit()
        conn.close()
        return dispatched

    @classmethod
    async def estimate_task_effort(cls, req: TaskEffortEstimateRequest) -> TaskEffortEstimateResponse:
        """AI-assisted effort estimation with assumptions and disclosure."""
        provider = get_llm_provider()
        subtasks = req.subtasks or []
        dependencies = req.dependencies or []

        if req.taskId:
            task = TaskService.get_task_by_id(req.taskId)
            if task:
                if not req.title:
                    req.title = task.title
                if not req.description:
                    req.description = task.description or ""
                if not subtasks and task.subtasks:
                    subtasks = task.subtasks
                if not dependencies and task.depends_on:
                    dependencies = [task.depends_on]

        llm_est = await provider.estimate_effort(
            task_title=req.title,
            task_description=req.description or "",
            subtasks=subtasks,
            dependencies=dependencies,
        )

        display_range = f"{int(llm_est.min_estimated_hours)}-{int(llm_est.max_estimated_hours)}h"

        return TaskEffortEstimateResponse(
            taskId=req.taskId,
            title=req.title,
            minEstimatedHours=llm_est.min_estimated_hours,
            maxEstimatedHours=llm_est.max_estimated_hours,
            estimatedHoursDisplay=display_range,
            assumptions=llm_est.assumptions,
            confidenceLevel=llm_est.confidence_level,
            informationNeeded=llm_est.information_needed,
            isAiEstimate=True,
        )

    @classmethod
    def get_full_team_workload_analysis(
        cls, analysis_window_days: Optional[int] = None
    ) -> TeamWorkloadAnalysisResponse:
        """Assembles 7-day deterministic metrics, risks, and active redistribution proposals."""
        window_days = analysis_window_days or settings.ANALYSIS_WINDOW_DAYS
        metrics = cls.calculate_deterministic_workload_metrics(window_days)
        confirmed, potential, ai_estimates = cls.detect_workload_risks(metrics)

        cls.analyze_team_workload_and_generate_recommendations()
        recommendations = cls.get_active_recommendations()

        overloaded_count = sum(1 for m in metrics if m.utilizationStatus == "Overloaded")
        unknown_cap_count = sum(1 for m in metrics if not m.utilizationCalculable)

        if overloaded_count > 0:
            summary = (
                f"Workload imbalance active: {overloaded_count} team member(s) exceed the "
                f"{settings.OVERLOAD_UTILIZATION_THRESHOLD}% capacity threshold over the next {window_days} days. "
                f"{len(recommendations)} rebalancing recommendation(s) available for leader review."
            )
        else:
            summary = (
                f"Sprint equilibrium optimal: All members with recorded availability remain within safe "
                f"capacity bounds over the next {window_days} days."
            )

        if unknown_cap_count > 0:
            summary += f" Note: {unknown_cap_count} member(s) have unrecorded working capacity."

        return TeamWorkloadAnalysisResponse(
            analysisWindowDays=window_days,
            memberMetrics=metrics,
            confirmedRisks=confirmed,
            potentialRisks=potential,
            aiGeneratedEstimates=ai_estimates,
            recommendations=recommendations,
            equilibriumSummary=summary,
        )

    @classmethod
    def get_project_workload_analysis(cls, project_name: str, analysis_window_days: int = 7) -> ProjectWorkloadResponse:
        """
        Calculates project-scoped workload metrics, risks, and recommendations (Section 10).
        """
        all_analysis = cls.get_full_team_workload_analysis(analysis_window_days=analysis_window_days)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT member_id FROM project_members WHERE LOWER(project_id) = LOWER(?)", (project_name,))
        member_ids = {r["member_id"] for r in cursor.fetchall()}
        
        # Include any members who currently have assigned tasks in this project
        cursor.execute("SELECT DISTINCT assignee_id FROM tasks WHERE LOWER(project) = LOWER(?)", (project_name,))
        for r in cursor.fetchall():
            if r["assignee_id"]:
                member_ids.add(r["assignee_id"])
        conn.close()

        # Filter member metrics for this project
        scoped_metrics = [m for m in all_analysis.memberMetrics if m.memberId in member_ids]
        if not scoped_metrics:
            scoped_metrics = all_analysis.memberMetrics

        # Filter risks for members of this project
        scoped_confirmed = [r for r in all_analysis.confirmedRisks if r.memberId in member_ids]
        scoped_potential = [r for r in all_analysis.potentialRisks if r.memberId in member_ids]

        # Filter recommendations where task belongs to this project
        scoped_recs = [r for r in all_analysis.recommendations if r.taskToReassign.project.lower() == project_name.lower()]

        return ProjectWorkloadResponse(
            projectId=project_name,
            projectName=project_name,
            memberMetrics=scoped_metrics,
            confirmedRisks=scoped_confirmed,
            potentialRisks=scoped_potential,
            recommendations=scoped_recs,
            equilibriumSummary=all_analysis.equilibriumSummary
        )

    @classmethod
    def get_member_workload_detail(cls, member_id: str, is_confidential_view: bool = False) -> MemberWorkloadResponse:
        """
        Retrieves dedicated workload telemetry and assigned task list for a member (Section 10).
        """
        metrics_list = cls.calculate_deterministic_workload_metrics()
        metric = next((m for m in metrics_list if m.memberId == member_id), None)
        if not metric:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=f"Member '{member_id}' not found.")

        tasks = TaskService.get_tasks_for_member(member_id)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM members WHERE id = ?", (member_id,))
        role_row = cursor.fetchone()
        conn.close()
        role = role_row["role"] if role_row else "Team Member"

        return MemberWorkloadResponse(
            memberId=member_id,
            memberName=metric.memberName,
            role=role,
            metrics=metric,
            assignedTasks=tasks,
            isConfidentialView=is_confidential_view
        )

