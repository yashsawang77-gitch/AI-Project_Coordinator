"""
Syncora AI - Notification & Leader Alert Service
Dispatches critical blocker alerts, workload imbalance warnings,
and deadline risk notifications to project leaders.
"""

import sqlite3
from datetime import datetime
from typing import List, Optional
from database import get_db_connection
from models.schemas import NotificationModel

class NotificationService:
    @staticmethod
    def _row_to_notif(row: sqlite3.Row) -> NotificationModel:
        return NotificationModel(
            id=row["id"],
            recipientId=row["recipient_id"],
            type=row["type"],
            title=row["title"],
            message=row["message"],
            urgency=row["urgency"],
            isRead=bool(row["is_read"]),
            createdAt=row["created_at"],
        )

    @classmethod
    def get_notifications(cls, recipient_id: Optional[str] = None) -> List[NotificationModel]:
        conn = get_db_connection()
        cursor = conn.cursor()
        if recipient_id:
            cursor.execute(
                "SELECT * FROM notifications WHERE recipient_id = ? ORDER BY created_at DESC LIMIT 50",
                (recipient_id,)
            )
        else:
            cursor.execute("SELECT * FROM notifications ORDER BY created_at DESC LIMIT 50")
        rows = cursor.fetchall()
        notifs = [cls._row_to_notif(r) for r in rows]
        conn.close()
        return notifs

    @classmethod
    def send_leader_alert(
        cls, title: str, message: str, urgency: str = "Critical", notif_type: str = "blocker", recipient_id: str = "mem-1"
    ) -> str:
        """Sends an in-app notification to the team leader."""
        import random
        conn = get_db_connection()
        cursor = conn.cursor()
        now_str = datetime.utcnow().isoformat()
        notif_id = f"notif-{int(datetime.utcnow().timestamp() * 1000)}-{random.randint(1000, 9999)}"

        cursor.execute("""
            INSERT INTO notifications (id, recipient_id, type, title, message, urgency, is_read, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (notif_id, recipient_id, notif_type, title, message, urgency, 0, now_str))

        conn.commit()
        conn.close()
        return notif_id

    @classmethod
    def mark_as_read(cls, notif_id: str) -> bool:
        """Marks a notification as read."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notif_id,))
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated

    @classmethod
    def mark_all_read(cls, recipient_id: Optional[str] = None) -> int:
        """Marks all notifications for a recipient (or all) as read."""
        conn = get_db_connection()
        cursor = conn.cursor()
        if recipient_id:
            cursor.execute("UPDATE notifications SET is_read = 1 WHERE recipient_id = ?", (recipient_id,))
        else:
            cursor.execute("UPDATE notifications SET is_read = 1")
        count = cursor.rowcount
        conn.commit()
        conn.close()
        return count

