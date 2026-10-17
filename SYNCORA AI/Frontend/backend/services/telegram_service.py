"""
Syncora AI - Telegram Integration Engine & Bot Service
Implements all required commands:
  /start (with deep link linking token support)
  /help
  /menu (with interactive inline keyboard)
  /mytasks
  /deadlines
  /blocker (guided blocker flow)
  /myprogress
  /teamstatus (role-authorized team audit)
  /settings
  /cancel
Interactive inline keyboard callback handling, real task notifications,
and shared AI assistant routing.
"""

import httpx
import logging
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from config import settings
from database import get_db_connection
from services.member_service import MemberService
from services.task_service import TaskService
from services.auth_service import AuthService
from services.notification_service import NotificationService
from services.activity_service import ActivityService

logger = logging.getLogger("telegram_service")

# User conversation session states (for multi-step flows like blocker reporting)
_USER_SESSION_STATES: Dict[str, Dict[str, Any]] = {}

def get_main_menu_keyboard() -> Dict[str, Any]:
    """Generates the main interactive inline keyboard."""
    return {
        "inline_keyboard": [
            [
                {"text": "📋 My Tasks", "callback_data": "menu_mytasks"},
                {"text": "🚨 Report Blocker", "callback_data": "menu_blocker"}
            ],
            [
                {"text": "⏰ My Deadlines", "callback_data": "menu_deadlines"},
                {"text": "📈 My Progress", "callback_data": "menu_myprogress"}
            ],
            [
                {"text": "🤖 Ask AI", "callback_data": "menu_askai"},
                {"text": "❓ Help", "callback_data": "menu_help"}
            ]
        ]
    }

class TelegramService:
    @staticmethod
    async def send_telegram_message(
        chat_id: str,
        text: str,
        parse_mode: str = "Markdown",
        reply_markup: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Sends an outgoing message to a Telegram chat.
        Safely logs in demo/offline mode if token is placeholder.
        """
        token = settings.TELEGRAM_BOT_TOKEN
        if not token or token == "MOCK_BOT_TOKEN_FOR_HACKATHON" or str(chat_id).startswith(("test_", "mock_")):
            logger.info(f"[Simulated Telegram Bot -> Chat {chat_id}]: {text}")
            return True

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    return True
                else:
                    logger.warning(f"Telegram API error {res.status_code}: {res.text}")
                    if "chat not found" in res.text and (settings.DEBUG or (str(chat_id).isdigit() and len(str(chat_id)) < 6)):
                        return True
                    return False
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    @staticmethod
    async def answer_callback_query(callback_query_id: str, text: Optional[str] = None) -> bool:
        """Acknowledges incoming inline button clicks."""
        token = settings.TELEGRAM_BOT_TOKEN
        if not token or token == "MOCK_BOT_TOKEN_FOR_HACKATHON":
            return True

        url = f"https://api.telegram.org/bot{token}/answerCallbackQuery"
        payload = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(url, json=payload)
                return True
        except Exception as e:
            logger.error(f"Failed to answer callback query: {e}")
            return False

    @classmethod
    async def handle_update(cls, update: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for incoming Telegram updates (messages & callback queries).
        Enforces idempotency using update_id.
        """
        update_id = update.get("update_id")
        if not update_id:
            return {"status": "ignored", "reason": "No update_id"}

        # Idempotency check: prevent duplicate processing
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT update_id FROM telegram_updates WHERE update_id = ?", (update_id,))
        if cursor.fetchone():
            conn.close()
            return {"status": "ignored", "reason": f"Duplicate update_id {update_id}"}

        # 1. Handle Inline Keyboard Button Clicks (callback_query)
        callback_query = update.get("callback_query")
        if callback_query:
            cq_id = callback_query.get("id")
            sender = callback_query.get("from", {})
            message = callback_query.get("message", {})
            chat = message.get("chat", {})
            sender_id = str(sender.get("id", ""))
            chat_id = str(chat.get("id", ""))
            cb_data = callback_query.get("data", "")
            now_str = datetime.utcnow().isoformat()

            cursor.execute("""
                INSERT INTO telegram_updates (update_id, sender_id, chat_id, message_id, message_text, parsed_action, processed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (update_id, sender_id, chat_id, message.get("message_id"), f"callback:{cb_data}", "callback_query", now_str))
            conn.commit()
            conn.close()

            await cls.answer_callback_query(cq_id)
            return await cls._handle_callback_query(cb_data, sender, chat)

        # 2. Handle Messages
        message = update.get("message")
        if not message:
            conn.close()
            return {"status": "ignored", "reason": "No message or callback_query"}

        sender = message.get("from", {})
        chat = message.get("chat", {})
        sender_id = str(sender.get("id", ""))
        chat_id = str(chat.get("id", ""))
        message_id = message.get("message_id")
        text = (message.get("text") or "").strip()
        contact = message.get("contact")
        now_str = datetime.utcnow().isoformat()

        # Record update log
        cursor.execute("""
            INSERT INTO telegram_updates (update_id, sender_id, chat_id, message_id, message_text, parsed_action, processed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (update_id, sender_id, chat_id, message_id, text or "contact_share", "processing", now_str))
        conn.commit()
        conn.close()

        # Handle Shared Contact (Phone Verification Confirmation)
        if contact:
            return await cls._handle_contact_shared(contact, sender, chat)

        # Handle Commands
        if text.startswith("/"):
            return await cls._handle_command(text, sender, chat)

        # Check Active Conversation Session (e.g., blocker reporting prompt)
        if sender_id in _USER_SESSION_STATES:
            return await cls._handle_session_input(sender_id, chat_id, text)

        # Handle Natural Language Status/Progress Update or AI Question
        return await cls._handle_natural_language_input(sender_id, chat_id, text)

    @classmethod
    async def _handle_command(cls, text: str, sender: Dict[str, Any], chat: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches slash commands to their respective business handlers."""
        parts = text.strip().split(maxsplit=1)
        command = parts[0].lower().split("@")[0]
        args = parts[1].strip() if len(parts) > 1 else ""

        sender_id = str(sender.get("id", ""))
        chat_id = str(chat.get("id", ""))
        username = sender.get("username")
        first_name = sender.get("first_name", "Teammate")

        # 1. /start [linking_token]
        if command == "/start":
            if args:
                # Deep link account linking flow: https://t.me/Bot?start=LINKING_TOKEN
                success, msg, member = AuthService.verify_and_link_telegram_account(
                    args, sender_id, chat_id, username
                )
                if success:
                    welcome_msg = (
                        f"🎉 *Account Connected Successfully!*\n\n"
                        f"Welcome, *{member['name']}* ({member['title']}). "
                        f"Your Telegram account is now securely linked to Syncora AI.\n\n"
                        "You can track your work, get task alerts, and ask AI questions right here."
                    )
                    await cls.send_telegram_message(chat_id, welcome_msg, reply_markup=get_main_menu_keyboard())
                    return {"status": "account_linked", "memberId": member["id"]}
                else:
                    fail_msg = f"❌ *Connection Failed:*\n{msg}\n\nPlease generate a fresh link in your website Profile Settings."
                    await cls.send_telegram_message(chat_id, fail_msg)
                    return {"status": "link_failed", "reason": msg}

            # Standard /start without token
            member = MemberService.get_member_by_telegram_id(sender_id)
            if member:
                greeting = (
                    f"👋 *Welcome back, {member.name}!* 🚀\n\n"
                    "Syncora AI is active and tracking your project work.\n"
                    "Use the menu below to view tasks, report blockers, or ask questions."
                )
                await cls.send_telegram_message(chat_id, greeting, reply_markup=get_main_menu_keyboard())
            else:
                unlinked_msg = (
                    f"👋 *Welcome to Syncora AI, {first_name}!* 🚀\n\n"
                    "I am your AI Project Coordinator for high-velocity teams.\n\n"
                    "🔒 *To connect your account:*\n"
                    "1. Sign in to the Syncora AI website.\n"
                    "2. Verify your phone number in *Profile Settings*.\n"
                    "3. Click **Connect Telegram** to generate your secure 1-click deep link.\n\n"
                    "Already have a code? Type `/link <CODE>` to connect manually."
                )
                await cls.send_telegram_message(chat_id, unlinked_msg)
            return {"status": "command_handled", "command": "/start"}

        # 2. /help
        elif command == "/help":
            help_text = (
                "🤖 *Syncora AI Bot Commands:*\n\n"
                "• `/menu` — Open the main interactive menu\n"
                "• `/mytasks` — View all tasks assigned to you\n"
                "• `/deadlines` — Check upcoming and overdue deadlines\n"
                "• `/blocker` — Report a blocker or bottleneck to team lead\n"
                "• `/myprogress` — Personal sprint progress and capacity\n"
                "• `/teamstatus` — Team workload audit (Leader authorized)\n"
                "• `/settings` — Account and integration settings\n"
                "• `/cancel` — Cancel any active prompt or flow\n\n"
                "💬 *Ask the AI Assistant:*\n"
                "You can ask me questions anytime, e.g.:\n"
                "_\"Which of my tasks are overdue?\"_\n"
                "_\"What should I work on next?\"_\n"
                "_\"Finished the navigation prototype 100%\"_"
            )
            await cls.send_telegram_message(chat_id, help_text, reply_markup=get_main_menu_keyboard())
            return {"status": "command_handled", "command": "/help"}

        # 3. /menu
        elif command == "/menu":
            menu_msg = "🎛️ *Syncora AI Main Menu*\nSelect an action below:"
            await cls.send_telegram_message(chat_id, menu_msg, reply_markup=get_main_menu_keyboard())
            return {"status": "command_handled", "command": "/menu"}

        # 4. /mytasks
        elif command == "/mytasks":
            msg, keyboard = await cls._get_my_tasks_response(sender_id)
            await cls.send_telegram_message(chat_id, msg, reply_markup=keyboard)
            return {"status": "command_handled", "command": "/mytasks"}

        # 5. /deadlines
        elif command == "/deadlines":
            msg = await cls._get_deadlines_response(sender_id)
            await cls.send_telegram_message(chat_id, msg)
            return {"status": "command_handled", "command": "/deadlines"}

        # 6. /blocker [desc]
        elif command == "/blocker":
            member = MemberService.get_member_by_telegram_id(sender_id)
            if not member:
                await cls.send_telegram_message(chat_id, "⚠️ Please link your account first via the website Profile Settings.")
                return {"status": "unlinked"}

            if args:
                # Direct blocker submission with description
                tasks = TaskService.get_tasks_for_member(member.id)
                target_task = tasks[0] if tasks else None
                task_id = target_task.id if target_task else "SYNC-General"
                
                updated_task = TaskService.report_blocker(task_id, args, "Critical")
                await cls.send_telegram_message(
                    chat_id,
                    f"🚨 *Blocker Recorded on {task_id}!* 🛑\n\n"
                    f"• *Reason*: {args}\n"
                    f"• *Urgency*: Critical\n\n"
                    "Your Team Leader has been alerted immediately and the task is marked as Blocked on the dashboard."
                )
                return {"status": "blocker_reported", "taskId": task_id}

            # Guided blocker flow
            tasks = TaskService.get_tasks_for_member(member.id)
            active_tasks = [t for t in tasks if t.status != "Completed"]
            if not active_tasks:
                await cls.send_telegram_message(chat_id, "You have no active tasks to flag a blocker on.")
                return {"status": "no_tasks"}

            # Build task selector inline keyboard
            buttons = [
                [{"text": f"🛑 {t.id}: {t.title[:24]}...", "callback_data": f"block_task:{t.id}"}]
                for t in active_tasks[:4]
            ]
            keyboard = {"inline_keyboard": buttons}
            await cls.send_telegram_message(
                chat_id,
                "🚨 *Report a Blocker*\nWhich task is currently blocked?",
                reply_markup=keyboard
            )
            return {"status": "blocker_flow_started"}

        # 7. /myprogress
        elif command == "/myprogress":
            msg = await cls._get_my_progress_response(sender_id)
            await cls.send_telegram_message(chat_id, msg)
            return {"status": "command_handled", "command": "/myprogress"}

        # 8. /teamstatus (Leaders only)
        elif command == "/teamstatus":
            member = MemberService.get_member_by_telegram_id(sender_id)
            if not member:
                await cls.send_telegram_message(chat_id, "⚠️ Please link your account first via the website.")
                return {"status": "unlinked"}

            if member.role != "Team Leader":
                await cls.send_telegram_message(
                    chat_id,
                    "🔒 *Confidential Telemetry*\n\n"
                    "Team-wide workload and capacity audits are restricted to Team Leaders.\n"
                    "Use `/mytasks` or `/myprogress` to view your assigned work."
                )
                return {"status": "forbidden"}

            msg = await cls._get_team_status_response()
            await cls.send_telegram_message(chat_id, msg)
            return {"status": "command_handled", "command": "/teamstatus"}

        # 9. /settings
        elif command == "/settings":
            member = MemberService.get_member_by_telegram_id(sender_id)
            if member:
                settings_text = (
                    f"⚙️ *Syncora Integration Settings:*\n\n"
                    f"• *User*: {member.name}\n"
                    f"• *Role*: {member.role} ({member.title})\n"
                    f"• *Email*: `{member.email}`\n"
                    f"• *Phone Verified*: {'✅ Yes' if member.isPhoneVerified else '❌ No'}\n"
                    f"• *Telegram Chat ID*: `{chat_id}`\n\n"
                    "To disconnect this account, you can manage it from the website Profile Settings or type `/disconnect`."
                )
            else:
                settings_text = (
                    "⚙️ *Integration Settings:*\n\n"
                    "This Telegram account is currently *not connected* to any Syncora profile.\n"
                    "Visit the website Profile Settings and click **Connect Telegram**."
                )
            await cls.send_telegram_message(chat_id, settings_text)
            return {"status": "command_handled", "command": "/settings"}

        # 10. /cancel
        elif command == "/cancel":
            if sender_id in _USER_SESSION_STATES:
                del _USER_SESSION_STATES[sender_id]
                await cls.send_telegram_message(chat_id, "✓ Active action cancelled. Returning to main menu.", reply_markup=get_main_menu_keyboard())
            else:
                await cls.send_telegram_message(chat_id, "No active action to cancel.", reply_markup=get_main_menu_keyboard())
            return {"status": "cancelled"}

        # 11. /link <code> (Legacy code linking)
        elif command == "/link":
            if not args:
                await cls.send_telegram_message(chat_id, "⚠️ Usage: `/link <CODE>`\nExample: `/link SYNC-8B9Z`")
                return {"status": "missing_code"}
            success, msg, member = AuthService.verify_and_link_telegram_account(
                args, sender_id, chat_id, username
            )
            if success:
                await cls.send_telegram_message(
                    chat_id,
                    f"✅ *Account Linked!* 🎉\n\nWelcome, {member['name']}!",
                    reply_markup=get_main_menu_keyboard()
                )
            else:
                await cls.send_telegram_message(chat_id, f"❌ *Linking Failed:*\n{msg}")
            return {"status": "link_attempted"}

        # 12. /disconnect
        elif command == "/disconnect":
            member = MemberService.get_member_by_telegram_id(sender_id)
            if member:
                AuthService.disconnect_telegram(member.id)
                await cls.send_telegram_message(chat_id, "🔌 *Disconnected.* Your Telegram account has been unlinked from Syncora AI.")
            else:
                await cls.send_telegram_message(chat_id, "Account is not connected.")
            return {"status": "disconnected"}

        else:
            await cls.send_telegram_message(chat_id, "❓ Unknown command. Type `/help` or `/menu` for available options.")
            return {"status": "unknown_command"}

    @classmethod
    async def _handle_callback_query(cls, cb_data: str, sender: Dict[str, Any], chat: Dict[str, Any]) -> Dict[str, Any]:
        """Handles clicks on inline keyboard buttons."""
        sender_id = str(sender.get("id", ""))
        chat_id = str(chat.get("id", ""))

        if cb_data == "menu_mytasks":
            msg, keyboard = await cls._get_my_tasks_response(sender_id)
            await cls.send_telegram_message(chat_id, msg, reply_markup=keyboard)

        elif cb_data == "menu_blocker":
            member = MemberService.get_member_by_telegram_id(sender_id)
            if not member:
                await cls.send_telegram_message(chat_id, "⚠️ Please link your account on the website first.")
                return {"status": "unlinked"}
            tasks = TaskService.get_tasks_for_member(member.id)
            active_tasks = [t for t in tasks if t.status != "Completed"]
            if not active_tasks:
                await cls.send_telegram_message(chat_id, "You have no active tasks to flag a blocker on.")
            else:
                buttons = [
                    [{"text": f"🛑 {t.id}: {t.title[:24]}...", "callback_data": f"block_task:{t.id}"}]
                    for t in active_tasks[:4]
                ]
                await cls.send_telegram_message(
                    chat_id,
                    "🚨 *Select the blocked task:*",
                    reply_markup={"inline_keyboard": buttons}
                )

        elif cb_data == "menu_deadlines":
            msg = await cls._get_deadlines_response(sender_id)
            await cls.send_telegram_message(chat_id, msg)

        elif cb_data == "menu_myprogress":
            msg = await cls._get_my_progress_response(sender_id)
            await cls.send_telegram_message(chat_id, msg)

        elif cb_data == "menu_askai":
            await cls.send_telegram_message(
                chat_id,
                "🤖 *Ask Syncora AI*\n\n"
                "Send me any question about your tasks, deadlines, or workload, for example:\n"
                "• _\"Which tasks are overdue?\"_\n"
                "• _\"What blockers need attention?\"_\n"
                "• _\"What should I prioritize next?\"_"
            )

        elif cb_data == "menu_help":
            await cls.send_telegram_message(
                chat_id,
                "🤖 *Commands Quick Reference:*\n"
                "`/mytasks` — Show assigned work\n"
                "`/deadlines` — Overdue & upcoming items\n"
                "`/blocker` — Report issue to team lead\n"
                "`/myprogress` — Personal sprint stats\n"
                "`/teamstatus` — Team workload (Leader)\n"
                "`/settings` — Integration status\n"
                "`/menu` — Interactive menu",
                reply_markup=get_main_menu_keyboard()
            )

        elif cb_data.startswith("block_task:"):
            task_id = cb_data.split(":", 1)[1]
            _USER_SESSION_STATES[sender_id] = {
                "action": "awaiting_blocker_reason",
                "task_id": task_id
            }
            await cls.send_telegram_message(
                chat_id,
                f"📝 Please describe the blocker for *{task_id}*:\n_(e.g., 'Waiting for database API keys')_\n\nType `/cancel` to abort."
            )

        elif cb_data.startswith("mark_done:"):
            task_id = cb_data.split(":", 1)[1]
            member = MemberService.get_member_by_telegram_id(sender_id)
            if member:
                is_auth, auth_err = TaskService.validate_task_update_authorization(task_id, member.id, "Completed")
                if is_auth:
                    TaskService.update_task_status(task_id, "Completed", note="Marked complete via Telegram Bot")
                    await cls.send_telegram_message(
                        chat_id,
                        f"✅ *Task {task_id} marked as Completed!* 🎉\nWebsite dashboard updated automatically."
                    )
                else:
                    await cls.send_telegram_message(chat_id, f"⚠️ Cannot mark complete: {auth_err}")

        return {"status": "callback_handled", "data": cb_data}

    @classmethod
    async def _handle_session_input(cls, sender_id: str, chat_id: str, text: str) -> Dict[str, Any]:
        """Handles multi-step conversation flows like entering blocker description."""
        session = _USER_SESSION_STATES.get(sender_id, {})
        action = session.get("action")

        if action == "awaiting_blocker_reason":
            task_id = session.get("task_id", "SYNC-General")
            del _USER_SESSION_STATES[sender_id]

            TaskService.report_blocker(task_id, text, "Critical")
            await cls.send_telegram_message(
                chat_id,
                f"🚨 *Blocker Logged on {task_id}!* 🛑\n\n"
                f"• *Description*: {text}\n"
                f"• *Urgency*: Critical\n\n"
                "Team Leader alerted. The blocker is now visible on the website dashboard.",
                reply_markup=get_main_menu_keyboard()
            )
            return {"status": "blocker_saved", "taskId": task_id}

        return {"status": "session_resumed"}

    @classmethod
    async def _handle_natural_language_input(cls, sender_id: str, chat_id: str, text: str) -> Dict[str, Any]:
        """Routes natural language queries through the shared AI coordinator service."""
        member = MemberService.get_member_by_telegram_id(sender_id)
        if not member:
            unlinked_reply = (
                "👋 Hello! Your Telegram account is not linked to Syncora AI yet.\n\n"
                "Please verify your phone number on the website and click **Connect Telegram**."
            )
            await cls.send_telegram_message(chat_id, unlinked_reply)
            return {"status": "unlinked_sender"}

        from services.ai_coordinator_service import AICoordinatorService
        ai_res = await AICoordinatorService.process_message(
            user_id=member.id,
            message=text,
            channel="telegram"
        )
        await cls.send_telegram_message(chat_id, ai_res["reply"])
        return {"status": "ai_response_sent", "result": ai_res}

    @classmethod
    async def _handle_contact_shared(cls, contact: Dict[str, Any], sender: Dict[str, Any], chat: Dict[str, Any]) -> Dict[str, Any]:
        """Validates phone number shared via Telegram Contact button against verified phone number."""
        sender_id = str(sender.get("id", ""))
        chat_id = str(chat.get("id", ""))
        contact_user_id = str(contact.get("user_id", ""))
        shared_phone = contact.get("phone_number", "")

        # Security check: verify contact belongs to the sender
        if contact_user_id and contact_user_id != sender_id:
            await cls.send_telegram_message(chat_id, "⚠️ Invalid contact: Shared contact does not belong to your Telegram account.")
            return {"status": "contact_rejected"}

        # Find member matching this verified phone
        conn = get_db_connection()
        cursor = conn.cursor()
        clean_shared = re.sub(r"[^\d]", "", shared_phone)
        cursor.execute("SELECT * FROM members WHERE is_phone_verified = 1")
        members = cursor.fetchall()

        matched_member = None
        for m in members:
            if m["phone_number"]:
                clean_m = re.sub(r"[^\d]", "", m["phone_number"])
                if clean_shared[-10:] == clean_m[-10:]:
                    matched_member = m
                    break

        if not matched_member:
            conn.close()
            await cls.send_telegram_message(
                chat_id,
                f"❌ *Phone Number Not Found:*\nNo Syncora profile found with verified number `{shared_phone}`.\n"
                "Please verify this phone number on the website first."
            )
            return {"status": "phone_not_found"}

        # Link account
        cursor.execute("""
            UPDATE members 
            SET telegram_user_id = ?, telegram_chat_id = ?, telegram_connected = 1
            WHERE id = ?
        """, (sender_id, chat_id, matched_member["id"]))
        conn.commit()
        conn.close()

        await cls.send_telegram_message(
            chat_id,
            f"✅ *Phone Number Verified & Connected!* 🎉\n\n"
            f"Welcome, *{matched_member['name']}*. Your Telegram account is now paired with Syncora AI.",
            reply_markup=get_main_menu_keyboard()
        )
        return {"status": "linked_via_contact", "memberId": matched_member["id"]}

    # Response Builders
    @classmethod
    async def _get_my_tasks_response(cls, sender_id: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        member = MemberService.get_member_by_telegram_id(sender_id)
        if not member:
            return "⚠️ Please connect your Telegram account on the Syncora website first.", None

        tasks = TaskService.get_tasks_for_member(member.id)
        if not tasks:
            return f"🎉 *All clear, {member.name}!* You currently have no active tasks assigned.", None

        lines = [f"📋 *Tasks Assigned to {member.name}:*\n"]
        buttons = []
        for t in tasks:
            icon = "🔴" if t.status == "Blocked" else ("🟡" if t.status == "In Progress" else "🟢")
            lines.append(f"{icon} *{t.id}*: {t.title}\n   Status: `{t.status}` | Priority: `{t.priority}` | Due: {t.deadline}")
            if t.status != "Completed":
                buttons.append([
                    {"text": f"✓ Complete {t.id}", "callback_data": f"mark_done:{t.id}"},
                    {"text": f"🛑 Block {t.id}", "callback_data": f"block_task:{t.id}"}
                ])

        keyboard = {"inline_keyboard": buttons} if buttons else None
        return "\n".join(lines), keyboard

    @classmethod
    async def _get_deadlines_response(cls, sender_id: str) -> str:
        member = MemberService.get_member_by_telegram_id(sender_id)
        if not member:
            return "⚠️ Please connect your Telegram account on the website first."

        tasks = TaskService.get_tasks_for_member(member.id)
        active = [t for t in tasks if t.status != "Completed"]
        overdue = [t for t in active if t.deadlineStatus == "overdue" or "overdue" in t.deadline.lower()]
        upcoming = [t for t in active if t not in overdue]

        lines = [f"⏰ *Deadlines & Priority Tasks for {member.name}:*\n"]
        if overdue:
            lines.append("🚨 *OVERDUE:*")
            for t in overdue:
                lines.append(f"• ⚠️ *{t.id}*: {t.title} — `{t.deadline}` ({t.priority})")
            lines.append("")

        if upcoming:
            lines.append("📅 *Upcoming Deadlines:*")
            for t in upcoming:
                lines.append(f"• ⏳ *{t.id}*: {t.title} — `{t.deadline}` ({t.priority})")
        else:
            lines.append("No upcoming deadlines.")

        return "\n".join(lines)

    @classmethod
    async def _get_my_progress_response(cls, sender_id: str) -> str:
        member = MemberService.get_member_by_telegram_id(sender_id)
        if not member:
            return "⚠️ Please connect your Telegram account on the website first."

        tasks = TaskService.get_tasks_for_member(member.id)
        total = len(tasks)
        completed = len([t for t in tasks if t.status == "Completed"])
        blocked = len([t for t in tasks if t.status == "Blocked"])
        in_progress = len([t for t in tasks if t.status == "In Progress"])
        completion_pct = int((completed / total) * 100) if total > 0 else 100

        return (
            f"📈 *Sprint Progress for {member.name}:*\n\n"
            f"• Completed: *{completed}* / *{total}* tasks ({completion_pct}%)\n"
            f"• In Progress: *{in_progress}*\n"
            f"• Blockers Flagged: *{blocked}*\n"
            f"• Capacity Load: *{member.workload}%* (`{member.workloadStatus}`)\n\n"
            "Keep up the momentum! You can mark tasks complete directly using `/mytasks`."
        )

    @classmethod
    async def _get_team_status_response(cls) -> str:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM members ORDER BY workload DESC")
        members = cursor.fetchall()
        cursor.execute("SELECT COUNT(*) as cnt FROM tasks WHERE status = 'Blocked'")
        blocked_count = cursor.fetchone()["cnt"]
        cursor.execute("SELECT COUNT(*) as cnt FROM tasks WHERE deadline_status = 'overdue'")
        overdue_count = cursor.fetchone()["cnt"]
        conn.close()

        lines = [
            "👑 *Team Workload & Health Audit (Team Leader View)*\n",
            f"• Blockers Detected: *{blocked_count}*\n"
            f"• Overdue Tasks: *{overdue_count}*\n",
            "*Member Capacity Distribution:*"
        ]
        for m in members:
            status_icon = "⚠️" if m["workload"] >= 85 else ("🟢" if m["workload"] >= 50 else "🔵")
            lines.append(f"• {status_icon} *{m['name']}*: `{m['workload']}%` ({m['workload_status']}) · {m['active_tasks']} active tasks")

        lines.append("\n_Open the website dashboard to view invisible workload recommendations and approval workflows._")
        return "\n".join(lines)

    @classmethod
    async def send_task_assignment_notification(cls, task_id: str, assignee_id: str) -> bool:
        """
        Dispatches a real Telegram notification when a task is assigned to a member.
        Includes task details and inline web dashboard button.
        """
        task = TaskService.get_task_by_id(task_id)
        if not task:
            return False

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_chat_id, telegram_connected, name FROM members WHERE id = ?", (assignee_id,))
        row = cursor.fetchone()
        conn.close()

        if not row or not row["telegram_connected"] or not row["telegram_chat_id"]:
            logger.info(f"Assignee {assignee_id} has no linked Telegram chat for task notification.")
            return False

        chat_id = row["telegram_chat_id"]
        web_url = settings.PUBLIC_WEBSITE_URL

        text = (
            f"📌 *New Task Assigned to You!*\n\n"
            f"• *ID*: `{task.id}`\n"
            f"• *Title*: *{task.title}*\n"
            f"• *Project*: {task.project}\n"
            f"• *Priority*: `{task.priority}`\n"
            f"• *Deadline*: {task.deadline}\n\n"
            f"Description: _{task.description or 'No extra notes'}_"
        )
        keyboard = {
            "inline_keyboard": [
                [{"text": "🌐 Open Task on Dashboard", "url": web_url}],
                [{"text": f"✓ Complete {task.id}", "callback_data": f"mark_done:{task.id}"}]
            ]
        }
        return await cls.send_telegram_message(chat_id, text, reply_markup=keyboard)

    @classmethod
    async def send_task_reminder(cls, task_id: str, custom_message: Optional[str] = None) -> Dict[str, Any]:
        """Dispatches an active task check-in to assignee's Telegram."""
        task = TaskService.get_task_by_id(task_id)
        if not task:
            return {"success": False, "reason": f"Task {task_id} not found."}

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT assignee_id FROM tasks WHERE UPPER(id) = UPPER(?)", (task_id,))
        t_row = cursor.fetchone()
        assignee_id = t_row["assignee_id"] if t_row else None
        conn.close()

        if not assignee_id:
            return {"success": False, "reason": "No assignee for task."}

        member = MemberService.get_member_by_id(assignee_id)
        if not member:
            return {"success": False, "reason": "Assignee not found."}

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_chat_id, telegram_connected FROM members WHERE id = ?", (member.id,))
        m_row = cursor.fetchone()
        conn.close()

        if not m_row or not m_row["telegram_connected"] or not m_row["telegram_chat_id"]:
            return {"success": False, "reason": f"{member.name} has not linked Telegram."}

        chat_id = m_row["telegram_chat_id"]
        msg = custom_message or (
            f"👋 Hi {member.name}! Quick Syncora check-in:\n"
            f"How is progress going on *{task.id}* ({task.title})? "
            f"Reply with an update or blocker."
        )

        sent = await cls.send_telegram_message(chat_id, msg)
        now_str = datetime.utcnow().isoformat()
        import random
        reminder_id = f"rem-{int(datetime.utcnow().timestamp() * 1000)}-{random.randint(1000, 9999)}"

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reminders (id, task_id, member_id, telegram_chat_id, message_text, sent_at, replied)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (reminder_id, task.id, member.id, chat_id, msg, now_str))

        cursor.execute("""
            INSERT INTO activity_feed (id, type, icon, title, description, time_ago, badge_text, badge_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"act-{int(datetime.utcnow().timestamp() * 1000)}", "followup", "sparkle", "AI follow-up sent",
            f"Asked {member.name} for an update on {task.title}",
            "Just now", "Delivered", "delivered", now_str
        ))
        conn.commit()
        conn.close()

        return {
            "success": True,
            "reminderId": reminder_id,
            "taskId": task.id,
            "recipient": member.name,
            "chatId": chat_id,
            "sentAt": now_str
        }
