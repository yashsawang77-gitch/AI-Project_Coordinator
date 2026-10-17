"""
Syncora AI - Activity & Event Logging Service
Standardized audit trail recorder for Section 11 events:
  - Telegram progress update received
  - AI interpretation accepted or clarification requested
  - Blocker identified or resolved
  - Workload analysis completed
  - Overload risk raised or cleared
  - Reassignment recommendation created
  - Recommendation approved or rejected
  - Task assignment changed

Stores timestamps, relevant IDs (task_id, member_id, project_id),
and concise, privacy-safe explanations.
"""

import time
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from database import get_db_connection

logger = logging.getLogger("activity_service")

# Default badge & icon mappings for standard event types
EVENT_CONFIGS = {
    "telegram_progress_received": {
        "icon": "MessageSquare",
        "badge_text": "Telegram",
        "badge_type": "info",
    },
    "ai_interpretation_accepted": {
        "icon": "Sparkles",
        "badge_text": "AI Verified",
        "badge_type": "success",
    },
    "ai_clarification_requested": {
        "icon": "HelpCircle",
        "badge_text": "Clarification",
        "badge_type": "warning",
    },
    "blocker_identified": {
        "icon": "AlertTriangle",
        "badge_text": "Blocked",
        "badge_type": "danger",
    },
    "blocker_resolved": {
        "icon": "CheckCircle2",
        "badge_text": "Resolved",
        "badge_type": "success",
    },
    "workload_analysis_completed": {
        "icon": "Activity",
        "badge_text": "Analysis",
        "badge_type": "primary",
    },
    "overload_risk_raised": {
        "icon": "ShieldAlert",
        "badge_text": "Overload Risk",
        "badge_type": "danger",
    },
    "overload_risk_cleared": {
        "icon": "ShieldCheck",
        "badge_text": "Risk Cleared",
        "badge_type": "success",
    },
    "recommendation_created": {
        "icon": "Shuffle",
        "badge_text": "Rebalance Proposal",
        "badge_type": "warning",
    },
    "recommendation_approved": {
        "icon": "CheckCheck",
        "badge_text": "Approved",
        "badge_type": "success",
    },
    "recommendation_rejected": {
        "icon": "XCircle",
        "badge_text": "Rejected",
        "badge_type": "secondary",
    },
    "task_assignment_changed": {
        "icon": "UserCheck",
        "badge_text": "Reassigned",
        "badge_type": "primary",
    },
}

class ActivityService:
    @classmethod
    def record_event(
        cls,
        event_type: str,
        title: str,
        description: str,
        task_id: Optional[str] = None,
        member_id: Optional[str] = None,
        project_id: Optional[str] = None,
        badge_text: Optional[str] = None,
        badge_type: Optional[str] = None,
        icon: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        external_conn=None,
    ) -> str:
        """
        Records an audit event in activity_feed.
        Accepts optional external_conn to operate within an active SQLite transaction.
        """
        event_id = f"act-{event_type}-{int(time.time() * 1000)}"
        cfg = EVENT_CONFIGS.get(event_type, {
            "icon": "Info",
            "badge_text": "Event",
            "badge_type": "primary",
        })

        chosen_icon = icon or cfg["icon"]
        chosen_badge_text = badge_text or cfg["badge_text"]
        chosen_badge_type = badge_type or cfg["badge_type"]
        time_ago = "Just now"
        created_at = datetime.utcnow().isoformat()
        metadata_str = json.dumps(metadata or {})

        conn = external_conn or get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO activity_feed (
                    id, type, icon, title, description, time_ago,
                    badge_text, badge_type, task_id, member_id, project_id, metadata, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_id,
                event_type,
                chosen_icon,
                title,
                description,
                time_ago,
                chosen_badge_text,
                chosen_badge_type,
                task_id,
                member_id,
                project_id,
                metadata_str,
                created_at,
            ))
            if external_conn is None:
                conn.commit()
            return event_id
        except Exception as e:
            logger.error(f"Failed to record activity event '{event_type}': {e}")
            return event_id
        finally:
            if external_conn is None:
                conn.close()

    @classmethod
    def get_events_for_task(cls, task_id: str, limit: int = 50):
        """Returns chronological activity history for a specific task."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM activity_feed
            WHERE task_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (task_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return rows

    @classmethod
    def get_events_for_project(cls, project_id: str, limit: int = 50):
        """Returns chronological activity history for a specific project."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM activity_feed
            WHERE project_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (project_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return rows
