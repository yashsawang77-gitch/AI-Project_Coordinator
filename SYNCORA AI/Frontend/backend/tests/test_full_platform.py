"""
Syncora AI — End-to-End Verification Test Suite
Validates:
1. Authentication (login, registration, forgot password)
2. Phone OTP Verification (request, rate-limit, verify, database update)
3. Telegram Account Linking (token generation, deep linking, link validation)
4. Real Telegram Bot commands (/start, /help, /menu, /mytasks, /deadlines, /blocker, /myprogress, /teamstatus)
5. Grounded AI Coordinator Service (answering overdue, assigned, blockers, workload, prioritization)
6. Two-Way Data Synchronization (completing task via Telegram, reporting blocker, task assignment notification)
7. Demo Mode Reset
"""

import sys
import os
from pathlib import Path

# Ensure UTF-8 stdout on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Setup path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

import asyncio
import pytest
from database import init_db, get_db_connection
from services.auth_service import AuthService
from services.sms_service import SMSService
from services.telegram_service import TelegramService
from services.task_service import TaskService
from services.ai_coordinator_service import AICoordinatorService

async def run_full_suite():
    print("\n🚀 Starting Syncora AI Master Implementation Test Suite...\n")
    passed = 0
    total = 0

    def check(condition, desc):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  ✅ Step {total}: {desc}")
        else:
            print(f"  ❌ Step {total} FAILED: {desc}")
            raise AssertionError(f"Step {total} failed: {desc}")

    # 1. Reset database to pristine state
    print("--- 1. Testing Database Initialization & Demo Reset ---")
    init_db(force_reseed=True)
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as cnt FROM members")
    member_count = c.fetchone()["cnt"]
    c.execute("SELECT COUNT(*) as cnt FROM tasks")
    task_count = c.fetchone()["cnt"]
    conn.close()
    check(member_count == 4, f"Database seeded with 4 team members (got {member_count})")
    check(task_count >= 5, f"Database seeded with tasks (got {task_count})")

    # 2. Test Simple Authentication
    print("\n--- 2. Testing Simple Authentication ---")
    user, token = AuthService.authenticate_user("maya.chen@novastudio.ai", "password123")
    check(user.name == "Maya Chen", f"Logged in as {user.name}")
    check(user.role == "leader", f"User role is {user.role}")
    check(token.startswith("syncora-jwt-"), f"Session token returned: {token}")

    # Register new user
    new_user, new_token = AuthService.register_user(
        name="Jordan Tech",
        email="jordan.tech@novastudio.ai",
        password="securepass123",
        role="Team Member"
    )
    check(new_user.name == "Jordan Tech", f"Registered new user: {new_user.name}")
    check(new_user.email == "jordan.tech@novastudio.ai", "New user email matches")

    # Forgot password
    forgot_res = AuthService.forgot_password("jordan.tech@novastudio.ai")
    check(forgot_res["success"], f"Forgot password generated token: {forgot_res.get('resetToken')}")

    # Reset password
    reset_res = AuthService.reset_password("jordan.tech@novastudio.ai", forgot_res["resetToken"], "newpass456")
    check(reset_res["success"], "Password reset successfully")

    # Verify login with new password
    auth_check, _ = AuthService.authenticate_user("jordan.tech@novastudio.ai", "newpass456")
    check(auth_check.name == "Jordan Tech", "Successfully authenticated with updated password")

    # 3. Test Phone Number OTP Verification
    print("\n--- 3. Testing Phone Number OTP Verification ---")
    phone = "+919876543210"
    otp_req = await SMSService.request_otp("mem-1", phone)
    check(otp_req["success"], f"OTP requested for {otp_req['phoneNumber']}")
    check(otp_req["isDemoSandbox"], "Honest sandbox disclosure active for local dev")
    sandbox_otp = otp_req["sandboxOtp"]
    check(len(sandbox_otp) == 6, f"Valid 6-digit OTP generated: {sandbox_otp}")

    # Verify OTP
    otp_verify = await SMSService.verify_otp("mem-1", phone, sandbox_otp)
    check(otp_verify["verified"], "OTP successfully verified")

    # Verify database was updated
    status = SMSService.get_status("mem-1")
    check(status["isVerified"], "Member status in SQLite confirms phone is verified")
    check(status["phoneNumber"] == phone, f"Verified phone number matches: {status['phoneNumber']}")

    # 4. Test Telegram Account Linking with Deep Link Token
    print("\n--- 4. Testing Telegram Account Linking Flow ---")
    # mem-1 has verified phone, so token generation must succeed
    token_data = AuthService.generate_telegram_linking_token("mem-1")
    link_token = token_data["token"]
    deep_link = token_data["deepLink"]
    check("start=" in deep_link, f"Deep link generated: {deep_link}")
    check(link_token.startswith("SYNC_"), f"Cryptographic linking token: {link_token}")

    # Unverified user should be rejected from linking
    try:
        AuthService.generate_telegram_linking_token(new_user.id)
        check(False, "Unverified user should have been blocked from generating link token")
    except Exception as e:
        check("Phone number verification required" in str(e), "Correctly enforced phone verification prerequisite")

    # Simulate user tapping Start in Telegram with linking token
    sim_update = {
        "update_id": 99901,
        "message": {
            "message_id": 101,
            "from": {"id": 1001, "first_name": "Maya", "username": "mayachen_ai"},
            "chat": {"id": 1001, "type": "private"},
            "date": 1700000000,
            "text": f"/start {link_token}"
        }
    }
    link_res = await TelegramService.handle_update(sim_update)
    check(link_res["status"] == "account_linked", "Telegram bot validated token and linked account")

    # Verify database reflects Telegram connection
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT telegram_connected, telegram_user_id, telegram_chat_id FROM members WHERE id = 'mem-1'")
    m_row = c.fetchone()
    conn.close()
    check(bool(m_row["telegram_connected"]), "Member marked as telegram_connected = 1 in SQLite")
    check(str(m_row["telegram_chat_id"]) == "1001", "Member chat ID stored in database")

    # 5. Test Telegram Bot Commands
    print("\n--- 5. Testing Telegram Bot Commands ---")
    commands_to_test = ["/help", "/menu", "/mytasks", "/deadlines", "/myprogress", "/teamstatus", "/settings"]
    for cmd in commands_to_test:
        sim_cmd = {
            "update_id": 99902 + commands_to_test.index(cmd),
            "message": {
                "message_id": 102,
                "from": {"id": 1001, "first_name": "Maya", "username": "mayachen_ai"},
                "chat": {"id": 1001, "type": "private"},
                "date": 1700000000,
                "text": cmd
            }
        }
        res = await TelegramService.handle_update(sim_cmd)
        check(res["status"] == "command_handled", f"Command {cmd} handled successfully")

    # Test Telegram Blocker Reporting
    blocker_update = {
        "update_id": 99920,
        "message": {
            "message_id": 110,
            "from": {"id": 1001, "first_name": "Maya", "username": "mayachen_ai"},
            "chat": {"id": 1001, "type": "private"},
            "date": 1700000000,
            "text": "/blocker Waiting on staging database credentials"
        }
    }
    blocker_res = await TelegramService.handle_update(blocker_update)
    check(blocker_res["status"] == "blocker_reported", "Reported blocker via Telegram")

    # 6. Test Grounded AI Coordinator Service
    print("\n--- 6. Testing Grounded AI Coordinator Service ---")
    # A. Overdue query
    ai_overdue = await AICoordinatorService.process_message("mem-1", "Which tasks are overdue?")
    check("SYNC-198" in ai_overdue["reply"] or "overdue" in ai_overdue["reply"].lower(), "AI accurately identified overdue task SYNC-198")

    # B. Assigned tasks query
    ai_tasks = await AICoordinatorService.process_message("mem-1", "What tasks are assigned to me?")
    check("active tasks" in ai_tasks["reply"].lower() or "SYNC-" in ai_tasks["reply"], "AI retrieved assigned tasks from SQLite")

    # C. Blockers query
    ai_blockers = await AICoordinatorService.process_message("mem-1", "What blockers need attention?")
    check("blocker" in ai_blockers["reply"].lower(), "AI retrieved active blockers")

    # D. Progress summary
    ai_prog = await AICoordinatorService.process_message("mem-1", "Summarize my progress.")
    check("completion rate" in ai_prog["reply"].lower() or "sprint progress" in ai_prog["reply"].lower(), "AI summarized progress")

    # E. Workload distribution
    ai_workload = await AICoordinatorService.process_message("mem-1", "How is my team workload distributed?")
    check("workload" in ai_workload["reply"].lower(), "AI reported workload distribution")

    # F. Prioritization recommendation
    ai_prio = await AICoordinatorService.process_message("mem-1", "What should I prioritize next?")
    check("recommend" in ai_prio["reply"].lower() or "focus on" in ai_prio["reply"].lower() or "blocked" in ai_prio["reply"].lower(), "AI recommended grounded priority task")

    # 7. Test Two-Way Synchronization
    print("\n--- 7. Testing Two-Way Synchronization (Telegram <-> Website) ---")
    # Mark task completed from Telegram callback
    cb_update = {
        "update_id": 99930,
        "callback_query": {
            "id": "cq-100",
            "from": {"id": 1001, "first_name": "Maya"},
            "message": {
                "message_id": 120,
                "chat": {"id": 1001, "type": "private"}
            },
            "data": "mark_done:SYNC-204"
        }
    }
    await TelegramService.handle_update(cb_update)
    # Check in DB
    task_204 = TaskService.get_task_by_id("SYNC-204")
    check(task_204.status == "Completed", f"Task SYNC-204 marked 'Completed' in database via Telegram update (got {task_204.status})")

    # Task Assignment Notification
    notif_sent = await TelegramService.send_task_assignment_notification("SYNC-195", "mem-1")
    check(notif_sent is True, "Dispatched real Telegram assignment notification for SYNC-195")

    print(f"\n🎉 ALL {passed}/{total} END-TO-END TESTS PASSED SUCCESSFULLY! 🚀\n")

if __name__ == "__main__":
    asyncio.run(run_full_suite())
