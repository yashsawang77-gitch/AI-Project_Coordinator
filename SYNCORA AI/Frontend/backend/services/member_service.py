"""
Syncora AI - Team Member Service
Manages member profiles, capacity tracking, and Telegram identity bindings.
"""

import sqlite3
from typing import List, Optional
from database import get_db_connection
from models.schemas import TeamMemberModel

class MemberService:
    @staticmethod
    def _row_to_member(row: sqlite3.Row) -> TeamMemberModel:
        return TeamMemberModel(
            id=row["id"],
            name=row["name"],
            initials=row["initials"],
            role=row["role"],
            title=row["title"],
            avatarBg=row["avatar_bg"],
            avatarColor=row["avatar_color"],
            online=bool(row["online"]),
            activeTasks=row["active_tasks"],
            completionRate=row["completion_rate"],
            workload=row["workload"],
            workloadStatus=row["workload_status"],
            workloadColor=row["workload_color"],
            email=row["email"],
            telegramHandle=row["telegram_handle"],
            telegramConnected=bool(row["telegram_connected"]),
            availableCapacityHours=float(row["available_capacity_hours"]) if ("available_capacity_hours" in row.keys() and row["available_capacity_hours"] is not None) else 35.0,
            skills=row["skills"] if "skills" in row.keys() else "General",
            phoneNumber=row["phone_number"] if "phone_number" in row.keys() else None,
            isPhoneVerified=bool(row["is_phone_verified"]) if "is_phone_verified" in row.keys() else False,
            phoneVerifiedAt=row["phone_verified_at"] if "phone_verified_at" in row.keys() else None,
        )

    @classmethod
    def get_all_members(cls) -> List[TeamMemberModel]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM members ORDER BY name ASC")
        rows = cursor.fetchall()
        members = [cls._row_to_member(r) for r in rows]
        conn.close()
        return members

    @classmethod
    def get_member_by_id(cls, member_id: str) -> Optional[TeamMemberModel]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM members WHERE id = ?", (member_id,))
        row = cursor.fetchone()
        conn.close()
        return cls._row_to_member(row) if row else None

    @classmethod
    def get_member_by_telegram_id(cls, telegram_user_id: str) -> Optional[TeamMemberModel]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM members WHERE telegram_user_id = ?", (str(telegram_user_id),))
        row = cursor.fetchone()
        conn.close()
        return cls._row_to_member(row) if row else None

    @classmethod
    def get_member_by_email(cls, email: str) -> Optional[TeamMemberModel]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM members WHERE LOWER(email) = LOWER(?)", (email.strip(),))
        row = cursor.fetchone()
        conn.close()
        return cls._row_to_member(row) if row else None
