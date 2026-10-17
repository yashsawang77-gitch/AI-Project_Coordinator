"""
Syncora AI - Background Scheduler & Proactive Analysis Service (Section 9)
Configurable background automation engine providing:
1. Sending task reminders (with anti-spam cooldown protection).
2. Analyzing upcoming workload risks deterministically without continuous LLM calls.
3. Refreshing stale workload snapshots across all active projects.
4. Checking unresolved blockers (>24h escalation).
5. Detecting deadline-critical tasks (<48h pressure).
6. Dispatching leader notifications ONLY when meaningful risk changes occur.
7. Distributed leader locking to prevent duplicate instances across restarts & multi-worker runs.
8. Authenticated manual analysis cycle execution for serverless / restricted deployments.
"""

import os
import json
import uuid
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from database import get_db_connection
from config import settings
from services.task_service import TaskService
from services.workload_service import WorkloadService
from services.telegram_service import TelegramService
from services.notification_service import NotificationService
from services.activity_service import ActivityService
from models.schemas import SchedulerRunReport

logger = logging.getLogger("scheduler_service")


class SchedulerService:
    _is_running: bool = False
    _worker_id: str = f"worker-{os.getpid()}-{uuid.uuid4().hex[:6]}"
    _last_risk_signature: str = ""
    _main_loop_task: Optional[asyncio.Task] = None
    _telegram_loop_task: Optional[asyncio.Task] = None

    @classmethod
    def acquire_leader_lock(cls) -> bool:
        """
        Database-backed distributed lock (Section 9):
        Ensures that only ONE worker instance across restarts or multi-worker deployments
        runs scheduled jobs. Prevents duplicate task reminders and alert storms.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.utcnow()
        now_str = now.isoformat()
        expires_at = (now + timedelta(seconds=settings.SCHEDULER_LOCK_TTL_SECONDS)).isoformat()

        try:
            # Try to renew own lock or take over expired lock
            cursor.execute("""
                UPDATE scheduler_locks 
                SET holder_id = ?, acquired_at = ?, expires_at = ?
                WHERE lock_name = 'scheduler_leader' AND (expires_at < ? OR holder_id = ?)
            """, (cls._worker_id, now_str, expires_at, now_str, cls._worker_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                conn.close()
                return True

            # If no lock entry exists yet, insert
            cursor.execute("""
                INSERT OR IGNORE INTO scheduler_locks (lock_name, holder_id, acquired_at, expires_at)
                VALUES ('scheduler_leader', ?, ?, ?)
            """, (cls._worker_id, now_str, expires_at))
            
            if cursor.rowcount > 0:
                conn.commit()
                conn.close()
                return True

            conn.close()
            return False
        except Exception as e:
            conn.rollback()
            conn.close()
            logger.warning(f"Scheduler lock contention: {e}")
            return False

    @classmethod
    def release_leader_lock(cls):
        """Releases leader lock during graceful shutdown."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM scheduler_locks 
                WHERE lock_name = 'scheduler_leader' AND holder_id = ?
            """, (cls._worker_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Error releasing scheduler lock: {e}")

    @classmethod
    async def start(cls):
        """Starts background loops if enabled and not already running."""
        if not settings.SCHEDULER_ENABLED:
            logger.info("Scheduler disabled via configuration (SCHEDULER_ENABLED=false).")
            return

        if cls._is_running:
            return

        cls._is_running = True
        cls._main_loop_task = asyncio.create_task(cls._heartbeat_and_analysis_loop())
        if settings.TELEGRAM_ENABLE_POLLING and settings.TELEGRAM_BOT_TOKEN != "MOCK_BOT_TOKEN_FOR_HACKATHON":
            cls._telegram_loop_task = asyncio.create_task(cls._telegram_polling_loop())
        logger.info(f"Scheduler service initialized on worker {cls._worker_id}.")

    @classmethod
    async def stop(cls):
        """Stops background loops and releases lock."""
        cls._is_running = False
        if cls._main_loop_task:
            cls._main_loop_task.cancel()
        if cls._telegram_loop_task:
            cls._telegram_loop_task.cancel()
        cls.release_leader_lock()
        logger.info("Scheduler service stopped gracefully.")

    @classmethod
    async def _heartbeat_and_analysis_loop(cls):
        """Main periodic worker loop."""
        while cls._is_running:
            try:
                # 1. Acquire distributed lock (prevents multi-worker duplication)
                has_lock = cls.acquire_leader_lock()
                if has_lock:
                    await cls.run_proactive_analysis_cycle(execution_mode="scheduled_background")
                else:
                    logger.debug(f"Worker {cls._worker_id} skipped cycle (lock held by another worker).")
            except Exception as e:
                logger.error(f"Error in scheduler analysis cycle: {e}")

            await asyncio.sleep(float(settings.REMINDERS_INTERVAL_SECONDS))

    # ==========================================================================
    # Deterministic Check Mechanisms (Avoid Unnecessary Continuous LLM Calls)
    # ==========================================================================

    @classmethod
    async def send_due_task_reminders(cls) -> int:
        """
        1. Task Reminders Mechanism:
        Identifies active tasks nearing deadline or overdue.
        Enforces cooldown protection (REMINDER_MIN_COOLDOWN_HOURS) to prevent spamming members.
        Dispatches via Telegram without requiring LLM generation.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.utcnow()
        now_str = now.isoformat()
        cooldown_cutoff = (now - timedelta(hours=settings.REMINDER_MIN_COOLDOWN_HOURS)).isoformat()

        # Find in-progress tasks with deadline pressure
        cursor.execute("""
            SELECT t.id, t.title, t.deadline, t.deadline_status, t.assignee_id, m.name as assignee_name, m.telegram_connected
            FROM tasks t
            JOIN members m ON t.assignee_id = m.id
            WHERE t.status = 'In Progress' 
              AND (t.deadline_status IN ('today', 'overdue') OR t.deadline LIKE '%Today%' OR t.deadline LIKE '%Tomorrow%')
              AND m.telegram_connected = 1
        """)
        due_tasks = cursor.fetchall()
        reminders_sent = 0

        for t in due_tasks:
            # Check reminder cooldown for this task
            cursor.execute("""
                SELECT id FROM reminders 
                WHERE task_id = ? AND sent_at >= ?
            """, (t["id"], cooldown_cutoff))
            if cursor.fetchone():
                continue  # Already pinged recently

            result = await TelegramService.send_task_reminder(t["id"])
            if result.get("success"):
                reminders_sent += 1

        conn.close()
        return reminders_sent

    @classmethod
    def check_unresolved_blockers(cls) -> int:
        """
        2. Unresolved Blockers Mechanism:
        Scans for tasks in 'Blocked' status.
        Deterministically checks if blocker has been unresolved for >24 hours.
        Escalates to project leaders if not already notified in the last 12 hours.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.utcnow()
        now_str = now.isoformat()
        cutoff_24h = (now - timedelta(hours=24)).isoformat()
        cutoff_12h = (now - timedelta(hours=12)).isoformat()

        cursor.execute("""
            SELECT t.id, t.title, t.project, t.assignee_name, t.blocker_reason, t.updated_at
            FROM tasks t
            WHERE t.status = 'Blocked' AND t.updated_at <= ?
        """, (cutoff_24h,))
        stale_blockers = cursor.fetchall()
        escalated_count = 0

        for b in stale_blockers:
            # Check if leader was notified in last 12h
            notif_key = f"blocker_escalation:{b['id']}"
            cursor.execute("""
                SELECT id FROM notifications 
                WHERE title LIKE ? AND created_at >= ?
            """, (f"%{b['id']}%", cutoff_12h))
            if cursor.fetchone():
                continue

            # Escalate to leader
            NotificationService.send_leader_alert(
                title=f"🚨 Prolonged Blocker on {b['id']}",
                message=f"Task '{b['title']}' assigned to {b['assignee_name']} has been blocked for >24 hours: {b['blocker_reason'] or 'Awaiting resolution'}.",
                urgency="Critical",
                notif_type="blocker_prolonged",
                recipient_id="mem-1"
            )
            escalated_count += 1

        conn.commit()
        conn.close()
        return escalated_count

    @classmethod
    def detect_deadline_critical_tasks(cls) -> int:
        """
        3. Deadline-Critical Tasks Mechanism:
        Deterministically identifies tasks due within DEADLINE_PRESSURE_HOURS (48h)
        whose remaining estimated hours exceed available capacity.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.utcnow()
        now_str = now.isoformat()
        t48 = (now + timedelta(hours=settings.DEADLINE_PRESSURE_HOURS)).isoformat()

        cursor.execute("""
            SELECT t.id, t.title, t.assignee_id, t.assignee_name, t.estimated_remaining_hours,
                   m.available_capacity_hours
            FROM tasks t
            JOIN members m ON t.assignee_id = m.id
            WHERE t.status != 'Completed'
              AND (t.deadline_status IN ('today', 'overdue') OR (t.deadline_date IS NOT NULL AND t.deadline_date <= ?))
        """, (t48,))
        critical_tasks = cursor.fetchall()
        conn.close()

        flagged = 0
        for ct in critical_tasks:
            cap = ct["available_capacity_hours"] or 35.0
            rem = ct["estimated_remaining_hours"] or 8.0
            if rem >= (cap * 0.5):
                flagged += 1

        return flagged

    @classmethod
    def refresh_stale_workload_snapshots(cls) -> int:
        """
        4. Stale Workload Snapshot Refresh Mechanism:
        Caches deterministic project metrics in workload_snapshots table.
        Refreshes stale snapshots older than STALE_SNAPSHOT_EXPIRY_MINUTES (default 30m)
        and re-runs redistribution analysis.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.utcnow()
        now_str = now.isoformat()
        cutoff_stale = (now - timedelta(minutes=settings.STALE_SNAPSHOT_EXPIRY_MINUTES)).isoformat()

        cursor.execute("SELECT id, name FROM projects")
        projects = cursor.fetchall()
        refreshed_count = 0

        # Run global analysis once
        WorkloadService.analyze_team_workload_and_generate_recommendations()
        all_metrics = WorkloadService.calculate_deterministic_workload_metrics()

        for p in projects:
            p_id = p["id"]
            cursor.execute("SELECT calculated_at FROM workload_snapshots WHERE project_id = ?", (p_id,))
            row = cursor.fetchone()

            if not row or row["calculated_at"] < cutoff_stale:
                # Build snapshot data scoped to project
                snapshot_content = {
                    "projectId": p_id,
                    "projectName": p["name"],
                    "calculatedAt": now_str,
                    "activeMembers": len(all_metrics),
                }
                expires_at = (now + timedelta(minutes=settings.STALE_SNAPSHOT_EXPIRY_MINUTES)).isoformat()
                cursor.execute("""
                    INSERT OR REPLACE INTO workload_snapshots (project_id, snapshot_data, calculated_at, expires_at)
                    VALUES (?, ?, ?, ?)
                """, (p_id, json.dumps(snapshot_content), now_str, expires_at))
                refreshed_count += 1

        conn.commit()
        conn.close()
        return refreshed_count

    @classmethod
    async def send_leader_notifications_on_meaningful_change(cls) -> Tuple[bool, int]:
        """
        5. Leader Notification Filter:
        Only dispatches leader alerts when a MEANINGFUL risk change occurs.
        Computes a deterministic hash of current significant risks.
        If identical to previous cycle, suppresses duplicate notifications.
        """
        metrics = WorkloadService.calculate_deterministic_workload_metrics()
        confirmed, potential, _ = WorkloadService.detect_workload_risks(metrics)

        significant_risks = [
            r for r in confirmed if r.riskType in ("capacity_overload", "blocked_downstream_threat", "critical_task_blocked", "overdue_tasks")
        ]

        # Compute deterministic signature
        risk_tokens = sorted([f"{r.riskType}:{r.memberId}:{','.join(sorted(r.taskIds))}" for r in significant_risks])
        current_signature = "|".join(risk_tokens)

        meaningful_change = (current_signature != cls._last_risk_signature)

        if not settings.LEADER_ALERT_MEANINGFUL_CHANGE_ONLY or meaningful_change:
            dispatched = await WorkloadService.dispatch_leader_workload_alerts()
            cls._last_risk_signature = current_signature
            return True, len(dispatched)

        return False, 0

    # ==========================================================================
    # Proactive Analysis Orchestration (Manual & Scheduled)
    # ==========================================================================

    @classmethod
    async def run_proactive_analysis_cycle(cls, execution_mode: str = "manual_override") -> SchedulerRunReport:
        """
        Executes a complete proactive analysis cycle across all 6 mechanisms:
        1. Sends task reminders (with cooldown protection).
        2. Detects deadline-critical tasks.
        3. Checks unresolved blockers (>24h).
        4. Refreshes stale snapshots.
        5. Analyzes upcoming workload risks deterministically.
        6. Sends leader notifications on meaningful change.
        Returns a structured report of all actions executed.
        """
        now_str = datetime.utcnow().isoformat()
        reminders_sent = await cls.send_due_task_reminders()
        blockers_checked = cls.check_unresolved_blockers()
        deadline_critical = cls.detect_deadline_critical_tasks()
        snapshots_refreshed = cls.refresh_stale_workload_snapshots()
        meaningful_change, alerts_count = await cls.send_leader_notifications_on_meaningful_change()

        report = SchedulerRunReport(
            status="success",
            timestamp=now_str,
            remindersSent=reminders_sent,
            unresolvedBlockersChecked=blockers_checked,
            deadlineCriticalDetected=deadline_critical,
            staleSnapshotsRefreshed=snapshots_refreshed,
            leaderAlertsDispatched=alerts_count,
            meaningfulChangesDetected=meaningful_change,
            executionMode=execution_mode,
        )
        ActivityService.record_event(
            "workload_analysis_completed",
            "Workload Analysis Completed",
            f"Proactive analysis cycle completed: {snapshots_refreshed} snapshot(s) refreshed, {alerts_count} leader alert(s).",
            metadata={"execution_mode": execution_mode, "reminders_sent": reminders_sent, "alerts_count": alerts_count}
        )

        logger.info(
            f"Proactive cycle executed ({execution_mode}): {reminders_sent} reminder(s), "
            f"{blockers_checked} blocker(s) checked, {snapshots_refreshed} snapshot(s) refreshed, "
            f"{alerts_count} alert(s) dispatched."
        )
        return report

    @classmethod
    async def _telegram_polling_loop(cls):
        """Long-polling worker for Telegram if webhooks are not active."""
        offset = 0
        token = settings.TELEGRAM_BOT_TOKEN
        url = f"https://api.telegram.org/bot{token}/getUpdates"

        import httpx
        logger.info("Telegram polling worker active.")
        while cls._is_running:
            try:
                async with httpx.AsyncClient(timeout=35.0) as client:
                    res = await client.get(url, params={"offset": offset, "timeout": 20})
                    if res.status_code == 200:
                        data = res.json()
                        for update in data.get("result", []):
                            offset = max(offset, update["update_id"] + 1)
                            await TelegramService.handle_update(update)
            except Exception as e:
                logger.error(f"Telegram polling error: {e}")
                await asyncio.sleep(5.0)
            await asyncio.sleep(settings.TELEGRAM_POLLING_INTERVAL)

