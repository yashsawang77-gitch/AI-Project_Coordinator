"""
Syncora AI - Shared Task Service
Acts as the single source of truth and validation engine for all task operations,
whether triggered from the React frontend, Telegram bot updates, or AI agents.
"""

import sqlite3
import random
import json
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from database import get_db_connection
from models.schemas import TaskModel, TaskCreateRequest
from services.activity_service import ActivityService

class TaskService:
    @staticmethod
    def _row_to_task(row: sqlite3.Row) -> TaskModel:
        subtasks_list = []
        if "subtasks" in row.keys() and row["subtasks"]:
            try:
                subtasks_list = json.loads(row["subtasks"])
            except Exception:
                subtasks_list = []

        return TaskModel(
            id=row["id"],
            title=row["title"],
            project=row["project"],
            assignee=row["assignee_name"],
            assigneeInitials=row["assignee_initials"],
            assigneeBg=row["assignee_bg"],
            assigneeTextColor=row["assignee_text_color"],
            deadline=row["deadline"],
            deadlineStatus=row["deadline_status"],
            status=row["status"],
            priority=row["priority"],
            leftBarColor=row["left_bar_color"],
            estimatedHours=row["estimated_hours"],
            confidence=row["confidence"],
            blockerReason=row["blocker_reason"],
            description=row["description"] or "",
            estimatedRemainingHours=float(row["estimated_remaining_hours"]) if ("estimated_remaining_hours" in row.keys() and row["estimated_remaining_hours"] is not None) else 8.0,
            explicitEstimateHours=float(row["explicit_estimate_hours"]) if ("explicit_estimate_hours" in row.keys() and row["explicit_estimate_hours"] is not None) else None,
            dependsOn=row["depends_on"] if "depends_on" in row.keys() else "",
            deadlineDate=row["deadline_date"] if "deadline_date" in row.keys() else None,
            subtasks=subtasks_list,
            completedWork=row["completed_work"] if "completed_work" in row.keys() else None,
            remainingWork=row["remaining_work"] if "remaining_work" in row.keys() else None,
        )

    @classmethod
    def get_all_tasks(cls, status_filter: Optional[str] = None) -> List[TaskModel]:
        """Retrieves all tasks, optionally filtered by status."""
        conn = get_db_connection()
        cursor = conn.cursor()

        if status_filter and status_filter.lower() != "all":
            # Map frontend tab values e.g. "in_progress" -> "In Progress"
            normalized = status_filter.replace("_", " ").title()
            cursor.execute(
                "SELECT * FROM tasks WHERE LOWER(status) = LOWER(?) ORDER BY updated_at DESC",
                (normalized,)
            )
        else:
            cursor.execute("SELECT * FROM tasks ORDER BY updated_at DESC")

        rows = cursor.fetchall()
        tasks = [cls._row_to_task(r) for r in rows]
        conn.close()
        return tasks

    @classmethod
    def get_task_by_id(cls, task_id: str) -> Optional[TaskModel]:
        """Fetches a specific task by ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE UPPER(id) = UPPER(?)", (task_id,))
        row = cursor.fetchone()
        conn.close()
        return cls._row_to_task(row) if row else None

    @classmethod
    def get_tasks_for_member(cls, member_id_or_name: str) -> List[TaskModel]:
        """Fetches all tasks assigned to a specific member ID or name."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM tasks 
            WHERE assignee_id = ? OR LOWER(assignee_name) = LOWER(?)
            ORDER BY CASE WHEN status = 'Blocked' THEN 1 WHEN status = 'In Progress' THEN 2 ELSE 3 END
        """, (member_id_or_name, member_id_or_name))
        rows = cursor.fetchall()
        tasks = [cls._row_to_task(r) for r in rows]
        conn.close()
        return tasks

    @classmethod
    def create_task(cls, req: TaskCreateRequest) -> TaskModel:
        """Creates a new task and recalculates assignee workloads."""
        conn = get_db_connection()
        cursor = conn.cursor()
        now_str = datetime.utcnow().isoformat()

        # Generate unique task ID
        cursor.execute("SELECT id FROM tasks WHERE id LIKE 'SYNC-%'")
        existing_ids = [r["id"] for r in cursor.fetchall()]
        next_num = 210
        while f"SYNC-{next_num}" in existing_ids:
            next_num += 1
        new_id = f"SYNC-{next_num}"

        # Resolve assignee metadata
        assignee_name = req.assignee or "Maya Chen"
        cursor.execute("SELECT * FROM members WHERE LOWER(name) = LOWER(?)", (assignee_name,))
        member_row = cursor.fetchone()
        
        assignee_id = member_row["id"] if member_row else None
        initials = "".join([part[0] for part in assignee_name.split() if part])[:2].upper()
        if member_row and member_row["initials"]:
            initials = member_row["initials"]

        priority = req.priority or "High"
        status = "In Progress"
        left_bar_color = "#f43f5e" if priority in ("High", "Critical") else "#f59e0b"

        cursor.execute("""
            INSERT INTO tasks (
                id, title, project, assignee_id, assignee_name, assignee_initials,
                assignee_bg, assignee_text_color, deadline, deadline_status,
                status, priority, left_bar_color, estimated_hours, confidence,
                blocker_reason, description, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            new_id, req.title, req.project or "Product Core", assignee_id,
            assignee_name, initials, "#18e5b4", "#090d16",
            req.deadline or "Tomorrow", "upcoming", status, priority,
            left_bar_color, req.estimatedHours or "6-10h", "90%",
            None, req.description or "", now_str, now_str
        ))

        # Log to activity feed
        act_id = f"act-{int(datetime.utcnow().timestamp() * 1000)}-{random.randint(1000, 9999)}"
        cursor.execute("""
            INSERT INTO activity_feed (id, type, icon, title, description, time_ago, badge_text, badge_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            act_id, "task_created", "sparkle", "New task scheduled",
            f"'{req.title}' created and assigned to {assignee_name}",
            "Just now", "Created", "verified", now_str
        ))

        conn.commit()
        conn.close()

        # Recalculate member workload
        if assignee_id:
            cls.sync_member_metrics(assignee_id)
            # Dispatch real Telegram assignment notification if linked
            try:
                import asyncio
                from services.telegram_service import TelegramService
                try:
                    loop = asyncio.get_running_loop()
                    if loop.is_running():
                        loop.create_task(TelegramService.send_task_assignment_notification(new_id, assignee_id))
                except RuntimeError:
                    pass
            except Exception as e:
                logger.warning(f"Could not dispatch telegram assignment notification: {e}")

        return cls.get_task_by_id(new_id)

    @classmethod
    def validate_task_update_authorization(
        cls, task_id: str, member_id: str, requested_status: str, is_almost_done: bool = False
    ) -> Tuple[bool, str]:
        """
        Independently verifies:
        1. Task exists and belongs to a project.
        2. Sender is authorized (assigned to task or Team Leader).
        3. Requested status is valid and permitted under project rules.
        4. Guardrail: Prevents marking 'Completed' if task is only 'almost done'.
        """
        if is_almost_done and requested_status.lower() == "completed":
            return False, "Project rule violation: Tasks cannot be marked 'Completed' while still 'almost done'."

        valid_statuses = {"in progress", "pending", "blocked", "completed"}
        if requested_status.strip().lower() not in valid_statuses:
            return False, f"Invalid status: '{requested_status}'. Allowed: Pending, In Progress, Blocked, Completed."

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE UPPER(id) = UPPER(?)", (task_id,))
        task_row = cursor.fetchone()
        if not task_row:
            conn.close()
            return False, f"Task {task_id} not found."

        if not task_row["project"]:
            conn.close()
            return False, f"Task {task_id} does not belong to any valid project."

        cursor.execute("SELECT * FROM members WHERE id = ?", (member_id,))
        member_row = cursor.fetchone()
        conn.close()

        if not member_row:
            return False, f"Member {member_id} not found."

        is_assignee = (task_row["assignee_id"] == member_id) or (task_row["assignee_name"].lower() == member_row["name"].lower())
        is_leader = (member_row["role"] == "Team Leader")

        if not (is_assignee or is_leader):
            return False, f"Unauthorized: {member_row['name']} is not assigned to {task_id} and is not a Team Leader."

        return True, "Authorized"

    @classmethod
    def update_task_status(
        cls,
        task_id: str,
        new_status: str,
        note: Optional[str] = None,
        completed_work: Optional[str] = None,
        remaining_work: Optional[str] = None,
        estimated_remaining_hours: Optional[float] = None
    ) -> Optional[TaskModel]:
        """Updates task status, validates transitions, and recalibrates team capacity."""
        conn = get_db_connection()
        cursor = conn.cursor()
        now_str = datetime.utcnow().isoformat()

        # Normalize status
        valid_statuses = {"in progress": "In Progress", "pending": "Pending", "blocked": "Blocked", "completed": "Completed"}
        normalized_status = valid_statuses.get(new_status.strip().lower(), new_status)

        # Determine left accent bar
        if normalized_status == "Completed":
            left_bar_color = "#10b981"
            deadline_status = "completed"
            if estimated_remaining_hours is None:
                estimated_remaining_hours = 0.0
            if remaining_work is None:
                remaining_work = ""
        elif normalized_status == "Blocked":
            left_bar_color = "#f43f5e"
            deadline_status = "overdue"
        elif normalized_status == "In Progress":
            left_bar_color = "#18e5b4"
            deadline_status = "upcoming"
        else:
            left_bar_color = "#f59e0b"
            deadline_status = "normal"

        # Check prior status for blocker resolution detection (Section 11)
        cursor.execute("SELECT status FROM tasks WHERE UPPER(id) = UPPER(?)", (task_id,))
        prior_row = cursor.fetchone()
        was_blocked = prior_row and prior_row["status"] == "Blocked"

        cursor.execute("""
            UPDATE tasks 
            SET status = ?, left_bar_color = ?, deadline_status = ?,
                completed_work = COALESCE(?, completed_work),
                remaining_work = COALESCE(?, remaining_work),
                estimated_remaining_hours = COALESCE(?, estimated_remaining_hours),
                updated_at = ?
            WHERE UPPER(id) = UPPER(?)
        """, (normalized_status, left_bar_color, deadline_status, completed_work, remaining_work, estimated_remaining_hours, now_str, task_id))

        if cursor.rowcount == 0:
            conn.close()
            return None

        # Fetch updated task
        cursor.execute("SELECT * FROM tasks WHERE UPPER(id) = UPPER(?)", (task_id,))
        task_row = cursor.fetchone()
        assignee_id = task_row["assignee_id"]
        task_title = task_row["title"]
        task_project = task_row["project"] if "project" in task_row.keys() else None

        # Increment AI metric status_changes
        cursor.execute("UPDATE ai_metrics SET status_changes = status_changes + 1, updated_at = ? WHERE id = 1", (now_str,))

        # Add to activity feed
        act_id = f"act-{int(datetime.utcnow().timestamp() * 1000)}-{random.randint(1000, 9999)}"
        cursor.execute("""
            INSERT INTO activity_feed (id, type, icon, title, description, time_ago, badge_text, badge_type, created_at, task_id, member_id, project_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            act_id, "status_update", "check" if normalized_status == "Completed" else "sparkle",
            "Status automatically updated",
            f"{task_title} → {normalized_status}",
            "Just now", "Verified", "verified", now_str,
            task_id, assignee_id, task_project
        ))

        # Record blocker resolved event if transitioning away from Blocked (Section 11)
        if was_blocked and normalized_status != "Blocked":
            ActivityService.record_event(
                "blocker_resolved",
                "Blocker Resolved",
                f"Blocker on {task_title} cleared. Status transitioned to {normalized_status}.",
                task_id=task_id,
                member_id=assignee_id,
                project_id=task_project,
                external_conn=conn,
            )

        conn.commit()
        conn.close()

        if assignee_id:
            cls.sync_member_metrics(assignee_id)

        return cls.get_task_by_id(task_id)

    @classmethod
    def report_blocker(cls, task_id: str, blocker_reason: str, urgency: str = "Critical") -> Optional[TaskModel]:
        """Marks a task as blocked, stores the reason, alerts leaders, and adjusts metrics."""
        conn = get_db_connection()
        cursor = conn.cursor()
        now_str = datetime.utcnow().isoformat()

        cursor.execute("""
            UPDATE tasks 
            SET status = 'Blocked', blocker_reason = ?, left_bar_color = '#f43f5e',
                priority = 'Critical', updated_at = ?
            WHERE UPPER(id) = UPPER(?)
        """, (blocker_reason, now_str, task_id))

        if cursor.rowcount == 0:
            conn.close()
            return None

        cursor.execute("SELECT * FROM tasks WHERE UPPER(id) = UPPER(?)", (task_id,))
        task_row = cursor.fetchone()
        assignee_name = task_row["assignee_name"]
        assignee_id = task_row["assignee_id"]
        title = task_row["title"]
        task_project = task_row["project"] if "project" in task_row.keys() else None

        # Increment blockers_detected in AI metrics
        cursor.execute("UPDATE ai_metrics SET blockers_detected = blockers_detected + 1, updated_at = ? WHERE id = 1", (now_str,))

        # Add to activity feed
        act_id = f"act-{int(datetime.utcnow().timestamp() * 1000)}-{random.randint(1000, 9999)}"
        cursor.execute("""
            INSERT INTO activity_feed (id, type, icon, title, description, time_ago, badge_text, badge_type, created_at, task_id, member_id, project_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            act_id, "blocker_detected", "warning",
            "New blocker detected",
            f"{assignee_name} flagged: {blocker_reason}",
            "Just now", "Needs attention", "attention", now_str,
            task_id, assignee_id, task_project
        ))

        # Record blocker identified event (Section 11)
        ActivityService.record_event(
            "blocker_identified",
            "Blocker Identified",
            f"{assignee_name} flagged blocker on {title}: \"{blocker_reason}\"",
            task_id=task_id,
            member_id=assignee_id,
            project_id=task_project,
            external_conn=conn,
        )

        # Create Leader Notification
        conn.commit()
        conn.close()

        from services.notification_service import NotificationService
        NotificationService.send_leader_alert(
            title=f"Blocker on {task_id}: {title}",
            message=f"{assignee_name} reported: {blocker_reason}",
            urgency=urgency,
            notif_type="blocker",
            recipient_id="mem-1"
        )

        if assignee_id:
            cls.sync_member_metrics(assignee_id)

        return cls.get_task_by_id(task_id)

    @classmethod
    def reassign_task(cls, task_id: str, new_assignee_name: str) -> Optional[TaskModel]:
        """Reassigns a task to another team member and updates both members' workloads."""
        conn = get_db_connection()
        cursor = conn.cursor()
        now_str = datetime.utcnow().isoformat()

        # Find member
        cursor.execute("SELECT * FROM members WHERE LOWER(name) = LOWER(?)", (new_assignee_name,))
        member = cursor.fetchone()
        if not member:
            conn.close()
            return None

        new_assignee_id = member["id"]
        initials = member["initials"]

        # Get old assignee ID
        cursor.execute("SELECT assignee_id, title FROM tasks WHERE UPPER(id) = UPPER(?)", (task_id,))
        task_row = cursor.fetchone()
        if not task_row:
            conn.close()
            return None
        old_assignee_id = task_row["assignee_id"]
        task_title = task_row["title"]

        cursor.execute("""
            UPDATE tasks
            SET assignee_id = ?, assignee_name = ?, assignee_initials = ?,
                status = 'In Progress', left_bar_color = '#18e5b4', updated_at = ?
            WHERE UPPER(id) = UPPER(?)
        """, (new_assignee_id, new_assignee_name, initials, now_str, task_id))

        # Log activity
        act_id = f"act-{int(datetime.utcnow().timestamp() * 1000)}-{random.randint(1000, 9999)}"
        cursor.execute("""
            INSERT INTO activity_feed (id, type, icon, title, description, time_ago, badge_text, badge_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            act_id, "task_reassigned", "sparkle",
            "Workload Rebalanced",
            f"Reassigned '{task_title}' to {new_assignee_name} with leader approval.",
            "Just now", "Delivered", "delivered", now_str
        ))

        conn.commit()
        conn.close()

        # Sync both members
        if old_assignee_id:
            cls.sync_member_metrics(old_assignee_id)
        cls.sync_member_metrics(new_assignee_id)

        # Dispatch real Telegram assignment notification to new assignee
        try:
            import asyncio
            from services.telegram_service import TelegramService
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    loop.create_task(TelegramService.send_task_assignment_notification(task_id, new_assignee_id))
            except RuntimeError:
                pass
        except Exception as e:
            logger.warning(f"Could not dispatch telegram reassignment notification: {e}")

        return cls.get_task_by_id(task_id)

    @classmethod
    def sync_member_metrics(cls, member_id: str):
        """Calculates actual active tasks, completion rate, and workload % for a member."""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as total FROM tasks WHERE assignee_id = ?", (member_id,))
        total = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) as completed FROM tasks WHERE assignee_id = ? AND status = 'Completed'", (member_id,))
        completed = cursor.fetchone()["completed"]

        cursor.execute("SELECT COUNT(*) as active FROM tasks WHERE assignee_id = ? AND status != 'Completed'", (member_id,))
        active = cursor.fetchone()["active"]

        cursor.execute("SELECT COUNT(*) as blocked FROM tasks WHERE assignee_id = ? AND status = 'Blocked'", (member_id,))
        blocked = cursor.fetchone()["blocked"]

        completion_rate = int((completed / total * 100)) if total > 0 else 80

        # Calculated workload metric formula: base 10% per active task + 15% per blocked task
        calculated_load = min(100, max(20, active * 12 + blocked * 15))
        if calculated_load >= 85:
            status = "Overloaded"
            color = "#f43f5e"
        elif calculated_load >= 60:
            status = "Optimal"
            color = "#18e5b4"
        else:
            status = "Available"
            color = "#18e5b4"

        cursor.execute("""
            UPDATE members 
            SET active_tasks = ?, completion_rate = ?, workload = ?, workload_status = ?, workload_color = ?
            WHERE id = ?
        """, (active, completion_rate, calculated_load, status, color, member_id))

        conn.commit()
        conn.close()
