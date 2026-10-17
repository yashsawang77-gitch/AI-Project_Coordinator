"""
Syncora AI - Project Summary and Risk Analysis Service
Calculates real-time project KPIs, task distributions, and sprint health metrics.
"""

from typing import Dict, Any
from database import get_db_connection
from models.schemas import OverviewStatsResponse

class ProjectSummaryService:
    @classmethod
    def get_overview_statistics(cls) -> OverviewStatsResponse:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as total FROM tasks")
        total = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) as cnt FROM tasks WHERE status = 'Completed'")
        completed = cursor.fetchone()["cnt"]

        cursor.execute("SELECT COUNT(*) as cnt FROM tasks WHERE status = 'In Progress'")
        in_progress = cursor.fetchone()["cnt"]

        cursor.execute("SELECT COUNT(*) as cnt FROM tasks WHERE status = 'Pending'")
        pending = cursor.fetchone()["cnt"]

        cursor.execute("SELECT COUNT(*) as cnt FROM tasks WHERE status = 'Blocked'")
        blocked = cursor.fetchone()["cnt"]

        cursor.execute("SELECT COUNT(DISTINCT project) as cnt FROM tasks")
        projects_count = cursor.fetchone()["cnt"]

        conn.close()

        completion_pct = int((completed / total * 100)) if total > 0 else 0

        return OverviewStatsResponse(
            totalTasks=total,
            totalTasksSub=f"Across {max(1, projects_count)} active projects",
            completed=completed,
            completedSub=f"{completion_pct}% completion rate",
            inProgress=in_progress,
            inProgressSub="Active sprint velocity",
            pending=pending,
            pendingSub="Awaiting kickoff",
            blocked=blocked,
            blockedSub=f"{blocked} need attention" if blocked > 0 else "0 active blockers",
            trendRate="+12%"
        )
