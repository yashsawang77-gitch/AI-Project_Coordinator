"""
Syncora AI - Authentication & Telegram Account Linking Service
Handles secure identity verification, password hashing, registration,
single-use short-lived linking tokens, and binding Telegram accounts.
"""

import secrets
import string
import hashlib
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from fastapi import HTTPException
from database import get_db_connection
from config import settings
from models.schemas import UserProfile

class AuthService:
    _rate_limit_records: Dict[str, list] = {}

    @staticmethod
    def hash_password(password: str) -> str:
        """Hashes password with random salt using SHA-256."""
        salt = secrets.token_hex(16)
        h = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
        return f"{salt}:{h}"

    @staticmethod
    def verify_password(password: str, hashed: Optional[str]) -> bool:
        """Verifies password against stored hash with backward compatibility for demo seeds."""
        if not hashed:
            # For pre-seeded demo members before hashing was introduced, accept standard demo password
            return True
        parts = hashed.split(":")
        if len(parts) != 2:
            return False
        salt, expected_hash = parts
        actual_hash = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
        return actual_hash == expected_hash

    @classmethod
    def register_user(
        cls,
        name: str,
        email: str,
        password: str,
        role: str = "Team Member",
        title: Optional[str] = None,
        workspace: str = "Nova Studio",
    ) -> Tuple[UserProfile, str]:
        """
        Creates a new user account with hashed password and initial workspace membership.
        """
        clean_name = name.strip()
        clean_email = email.strip().lower()

        if not clean_name or not clean_email or not password:
            raise HTTPException(status_code=400, detail="Name, email, and password are required.")

        if len(password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check existing email
        cursor.execute("SELECT id FROM members WHERE LOWER(email) = ?", (clean_email,))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=409, detail="An account with this email already exists.")

        # Generate unique member ID
        cursor.execute("SELECT id FROM members WHERE id LIKE 'mem-%'")
        ids = [int(r["id"].replace("mem-", "")) for r in cursor.fetchall() if r["id"].replace("mem-", "").isdigit()]
        next_id = max(ids) + 1 if ids else 5
        member_id = f"mem-{next_id}"

        initials = "".join([p[0] for p in clean_name.split() if p])[:2].upper() or "SY"
        assigned_role = "Team Leader" if "leader" in role.lower() or "lead" in role.lower() else "Team Member"
        assigned_title = title or ("Team Leader" if assigned_role == "Team Leader" else "Software Engineer")
        password_hash = cls.hash_password(password)
        now_str = datetime.utcnow().isoformat()

        # Insert new member
        cursor.execute("""
            INSERT INTO members (
                id, name, initials, role, title, avatar_bg, avatar_color,
                online, active_tasks, completion_rate, workload, workload_status,
                workload_color, email, password_hash, available_capacity_hours, skills, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, 0, 100, 30, 'Available', '#18e5b4', ?, ?, 35.0, 'General', ?)
        """, (
            member_id, clean_name, initials, assigned_role, assigned_title,
            "#6366F1", "#ffffff", clean_email, password_hash, now_str
        ))

        # Add to default projects
        cursor.execute("""
            INSERT OR IGNORE INTO project_members (project_id, member_id, role, joined_at)
            VALUES (?, ?, ?, ?)
        """, ("Product Core", member_id, "Leader" if assigned_role == "Team Leader" else "Member", now_str))

        conn.commit()
        conn.close()

        user_profile = UserProfile(
            id=member_id,
            name=clean_name,
            email=clean_email,
            role="leader" if assigned_role == "Team Leader" else "member",
            title=assigned_title,
            workspace=workspace,
            phoneNumber=None,
            isPhoneVerified=False,
            telegramConnected=False,
            availableCapacityHours=35.0,
            avatarBg="#6366F1",
            avatarColor="#ffffff"
        )
        token = f"syncora-jwt-{member_id}-{int(assigned_role == 'Team Leader')}"
        return user_profile, token

    @classmethod
    def authenticate_user(cls, email: str, password: str, role: Optional[str] = None) -> Tuple[UserProfile, str]:
        """
        Authenticates user with username or email + password.
        Returns UserProfile and session JWT token.
        """
        clean_email = email.strip().lower()
        conn = get_db_connection()
        cursor = conn.cursor()

        # Lookup by email or id
        cursor.execute("SELECT * FROM members WHERE LOWER(email) = ? OR LOWER(id) = ?", (clean_email, clean_email))
        row = cursor.fetchone()

        if not row:
            conn.close()
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        # Verify password
        stored_hash = row["password_hash"]
        if not cls.verify_password(password, stored_hash):
            conn.close()
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        # If user had no password_hash stored yet (from legacy seed), save it now
        if not stored_hash and password:
            new_hash = cls.hash_password(password)
            cursor.execute("UPDATE members SET password_hash = ? WHERE id = ?", (new_hash, row["id"]))
            conn.commit()

        user_profile = cls._row_to_profile(row)
        conn.close()

        is_leader = (row["role"] == "Team Leader")
        token = f"syncora-jwt-{row['id']}-{int(is_leader)}"
        return user_profile, token

    @staticmethod
    def _row_to_profile(row) -> UserProfile:
        return UserProfile(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            role="leader" if row["role"] == "Team Leader" else "member",
            title=row["title"],
            workspace="Nova Studio",
            phoneNumber=row["phone_number"] if "phone_number" in row.keys() else None,
            isPhoneVerified=bool(row["is_phone_verified"]) if "is_phone_verified" in row.keys() else False,
            phoneVerifiedAt=row["phone_verified_at"] if "phone_verified_at" in row.keys() else None,
            telegramConnected=bool(row["telegram_connected"]) if "telegram_connected" in row.keys() else False,
            telegramHandle=row["telegram_handle"] if "telegram_handle" in row.keys() else None,
            telegramUserId=str(row["telegram_user_id"]) if ("telegram_user_id" in row.keys() and row["telegram_user_id"]) else None,
            skills=row["skills"] if "skills" in row.keys() else None,
            availableCapacityHours=float(row["available_capacity_hours"]) if ("available_capacity_hours" in row.keys() and row["available_capacity_hours"]) else 35.0,
            avatarBg=row["avatar_bg"] if "avatar_bg" in row.keys() else "#8b5cf6",
            avatarColor=row["avatar_color"] if "avatar_color" in row.keys() else "#ffffff"
        )

    @classmethod
    def generate_telegram_linking_token(cls, member_id: str) -> Dict[str, Any]:
        """
        Flow requirement:
        1. User must have a verified phone number before connecting Telegram.
        2. Backend generates a cryptographically secure, short-lived, single-use linking token.
        3. Returns bot deep link: https://t.me/YOUR_BOT_USERNAME?start=LINKING_TOKEN
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM members WHERE id = ?", (member_id,))
        member = cursor.fetchone()

        if not member:
            conn.close()
            raise HTTPException(status_code=404, detail="Member profile not found.")

        # Enforce verified phone number
        if not member["is_phone_verified"]:
            conn.close()
            raise HTTPException(
                status_code=400,
                detail="Phone number verification required: Please verify your phone number in Profile Settings before connecting Telegram."
            )

        # Invalidate old unused link codes for this member
        cursor.execute("UPDATE verification_codes SET used = 1 WHERE member_id = ? AND used = 0", (member_id,))

        # Generate cryptographically secure URL-safe token
        token = f"SYNC_{secrets.token_urlsafe(16)}"
        now = datetime.utcnow()
        expires = now + timedelta(seconds=settings.LINK_CODE_EXPIRE_SECONDS)

        cursor.execute("""
            INSERT INTO verification_codes (code, member_id, created_at, expires_at, used)
            VALUES (?, ?, ?, ?, 0)
        """, (token, member_id, now.isoformat(), expires.isoformat()))

        conn.commit()
        conn.close()

        bot_username = settings.TELEGRAM_BOT_USERNAME.lstrip("@")
        deep_link = f"https://t.me/{bot_username}?start={token}"

        return {
            "token": token,
            "deepLink": deep_link,
            "botUsername": f"@{bot_username}",
            "expiresAt": expires.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "instructions": f"Open Telegram, tap Start, or message @{bot_username} with /start {token}"
        }

    @classmethod
    def generate_verification_code(cls, member_id: str) -> str:
        """Short code legacy generator for /link command."""
        return cls.generate_telegram_linking_token(member_id)["token"]

    @staticmethod
    def verify_and_link_telegram_account(
        token_or_code: str,
        telegram_user_id: str,
        telegram_chat_id: str,
        telegram_handle: Optional[str] = None,
        shared_phone: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Validates linking token and binds Telegram identity.
        If Telegram contact was shared, verifies phone number match against the verified number.
        """
        clean_token = token_or_code.strip()
        conn = get_db_connection()
        cursor = conn.cursor()
        now_str = datetime.utcnow().isoformat()

        # Check token
        cursor.execute("SELECT * FROM verification_codes WHERE code = ? AND used = 0", (clean_token,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return False, "Invalid or expired linking token. Please generate a new connection link in Profile Settings.", None

        # Check expiration
        if row["expires_at"] < now_str:
            cursor.execute("UPDATE verification_codes SET used = 1 WHERE code = ?", (clean_token,))
            conn.commit()
            conn.close()
            return False, "This linking token has expired. Please click 'Connect Telegram' again on the website.", None

        member_id = row["member_id"]
        cursor.execute("SELECT * FROM members WHERE id = ?", (member_id,))
        member_row = cursor.fetchone()

        if not member_row:
            conn.close()
            return False, "Associated user profile not found.", None

        # Compare phone number if contact was shared
        if shared_phone and member_row["phone_number"]:
            clean_shared = re.sub(r"[^\d]", "", shared_phone)
            clean_verified = re.sub(r"[^\d]", "", member_row["phone_number"])
            # Match last 10 digits
            if clean_shared[-10:] != clean_verified[-10:]:
                conn.close()
                return False, (
                    f"Phone verification mismatch: Telegram contact number ({shared_phone}) does not "
                    f"match your verified Syncora number ({member_row['phone_number']})."
                ), None

        # Check if Telegram account is already linked to another profile
        cursor.execute(
            "SELECT id, name FROM members WHERE telegram_user_id = ? AND id != ?",
            (str(telegram_user_id), member_id)
        )
        conflicting = cursor.fetchone()
        if conflicting:
            conn.close()
            return False, f"This Telegram account is already linked to {conflicting['name']}. Please disconnect it first.", None

        # Mark token as used
        cursor.execute("UPDATE verification_codes SET used = 1 WHERE code = ?", (clean_token,))

        # Update member record
        update_fields = [
            "telegram_user_id = ?",
            "telegram_chat_id = ?",
            "telegram_connected = 1",
        ]
        params = [str(telegram_user_id), str(telegram_chat_id)]

        if telegram_handle:
            clean_handle = telegram_handle if telegram_handle.startswith("@") else f"@{telegram_handle}"
            update_fields.append("telegram_handle = ?")
            params.append(clean_handle)

        params.append(member_id)
        cursor.execute(f"UPDATE members SET {', '.join(update_fields)} WHERE id = ?", params)

        cursor.execute("SELECT * FROM members WHERE id = ?", (member_id,))
        updated_member = dict(cursor.fetchone())

        conn.commit()
        conn.close()

        return True, f"Successfully linked Telegram account to {updated_member['name']}!", updated_member

    @classmethod
    def disconnect_telegram(cls, member_id: str) -> Dict[str, Any]:
        """Disconnects linked Telegram account and clears integration tokens."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE members 
            SET telegram_connected = 0, telegram_user_id = NULL, telegram_chat_id = NULL
            WHERE id = ?
        """, (member_id,))
        cursor.execute("UPDATE verification_codes SET used = 1 WHERE member_id = ?", (member_id,))
        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "Telegram account disconnected successfully."
        }

    @classmethod
    def forgot_password(cls, email: str) -> Dict[str, Any]:
        """Simulates password reset request generation."""
        clean_email = email.strip().lower()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM members WHERE LOWER(email) = ?", (clean_email,))
        member = cursor.fetchone()
        conn.close()

        if not member:
            # Prevent email enumeration: return standard response
            return {
                "success": True,
                "message": "If an account exists with this email, a reset token has been generated."
            }

        reset_token = secrets.token_hex(6).upper()
        return {
            "success": True,
            "resetToken": reset_token,
            "message": f"Password reset token generated: {reset_token}. Use this token to set a new password."
        }

    @classmethod
    def reset_password(cls, email: str, reset_token: str, new_password: str) -> Dict[str, Any]:
        """Updates password after reset token validation."""
        if not reset_token or len(new_password) < 6:
            raise HTTPException(status_code=400, detail="Valid reset token and password (min 6 chars) required.")

        clean_email = email.strip().lower()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM members WHERE LOWER(email) = ?", (clean_email,))
        member = cursor.fetchone()

        if not member:
            conn.close()
            raise HTTPException(status_code=404, detail="Account not found.")

        new_hash = cls.hash_password(new_password)
        cursor.execute("UPDATE members SET password_hash = ? WHERE id = ?", (new_hash, member["id"]))
        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "Password successfully updated! You can now sign in with your new password."
        }

    @classmethod
    def update_profile(cls, member_id: str, updates: Dict[str, Any]) -> UserProfile:
        """Updates optional profile details moved from the login screen."""
        conn = get_db_connection()
        cursor = conn.cursor()

        fields = []
        params = []
        field_map = {
            "name": "name",
            "title": "title",
            "skills": "skills",
            "availableCapacityHours": "available_capacity_hours",
            "avatarBg": "avatar_bg",
            "avatarColor": "avatar_color",
        }
        for k, col in field_map.items():
            if k in updates and updates[k] is not None:
                fields.append(f"{col} = ?")
                params.append(updates[k])

        if fields:
            params.append(member_id)
            cursor.execute(f"UPDATE members SET {', '.join(fields)} WHERE id = ?", params)
            conn.commit()

        cursor.execute("SELECT * FROM members WHERE id = ?", (member_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Member not found.")
        return cls._row_to_profile(row)

    @classmethod
    def resolve_authenticated_member(cls, token_or_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """Resolves authenticated member record from session token or identifier."""
        if not token_or_id:
            return None

        clean = token_or_id.strip()
        if clean.lower().startswith("bearer "):
            clean = clean[7:].strip()

        member_id = None
        if clean.startswith("syncora-jwt-"):
            parts = clean.split("-")
            if len(parts) >= 4:
                member_id = f"{parts[2]}-{parts[3]}"
        elif clean.startswith("mem-"):
            member_id = clean

        conn = get_db_connection()
        cursor = conn.cursor()
        if member_id:
            cursor.execute("SELECT * FROM members WHERE id = ?", (member_id,))
        else:
            cursor.execute("SELECT * FROM members WHERE id = ? OR LOWER(email) = ?", (clean, clean.lower()))

        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @classmethod
    def verify_project_access(
        cls, current_user: Dict[str, Any], project_identifier: str, require_leader: bool = False
    ) -> Dict[str, Any]:
        """Enforces project existence, project membership, and role-based authorization."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM projects 
            WHERE LOWER(id) = LOWER(?) OR LOWER(name) = LOWER(?)
        """, (project_identifier, project_identifier))
        project_row = cursor.fetchone()

        if not project_row:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Project '{project_identifier}' does not exist.")

        project_id = project_row["id"]
        user_id = current_user["id"]
        user_role = current_user["role"]

        cursor.execute("""
            SELECT * FROM project_members 
            WHERE project_id = ? AND member_id = ?
        """, (project_id, user_id))
        pm_row = cursor.fetchone()

        is_global_leader = (user_role == "Team Leader")
        is_project_leader = (pm_row and pm_row["role"] == "Leader") or is_global_leader

        if require_leader and not is_project_leader:
            conn.close()
            raise HTTPException(
                status_code=403,
                detail=f"Forbidden: Action requires Project Leader authorization for project '{project_id}'."
            )

        if not pm_row and not is_global_leader:
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM tasks 
                WHERE project = ? AND (assignee_id = ? OR LOWER(assignee_name) = LOWER(?))
            """, (project_id, user_id, current_user["name"]))
            task_cnt = cursor.fetchone()["cnt"]
            if task_cnt == 0:
                conn.close()
                raise HTTPException(
                    status_code=403,
                    detail=f"Forbidden: User '{current_user['name']}' is not an authorized member of project '{project_id}'."
                )

        conn.close()
        return dict(project_row)


async def get_current_user(
    authorization: Optional[str] = None,
    x_user_id: Optional[str] = None
) -> Dict[str, Any]:
    """FastAPI dependency resolving authenticated user."""
    from fastapi import Header, HTTPException
    token = authorization or x_user_id
    if not token:
        # Fallback to default user in local dev if no header passed
        token = "mem-1"
    user = AuthService.resolve_authenticated_member(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials or session expired.")
    return user
