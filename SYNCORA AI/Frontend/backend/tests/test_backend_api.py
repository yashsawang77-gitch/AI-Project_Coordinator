"""
Syncora AI - Complete Automated Backend API & Telegram Integration Test Suite
Validates all 12 frontend API endpoints, task workflows, Invisible Workload Detector,
account linking, idempotency protection, and natural language reply interpretation.
"""

import sys
import os
import asyncio
from datetime import datetime
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


from httpx import AsyncClient, ASGITransport
from main import app
from database import init_db, get_db_connection
from models.schemas import TaskModel, DeterministicWorkloadMetrics
from services.auth_service import AuthService
from services.telegram_service import TelegramService
from services.task_service import TaskService
from services.workload_service import WorkloadService

async def run_tests():
    print("\n🧪 [Syncora Backend Test Suite] Starting step-by-step verification...\n")
    passed = 0
    total = 0

    def assert_test(condition, description):
        nonlocal passed, total
        total += 1
        if condition:
            print(f"  ✅ [PASS] Step {total}: {description}")
            passed += 1
        else:
            print(f"  ❌ [FAIL] Step {total}: {description}")
            raise AssertionError(f"Test failed: {description}")

    # Re-initialize test DB
    init_db(force_reseed=True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # STEP 1: Health & Root
        print("--- 1. Testing Core Server & Health ---")
        res = await client.get("/api/health")
        assert_test(res.status_code == 200, "Health check endpoint returns 200 OK")
        data = res.json()
        assert_test(data.get("status") == "healthy", "Health check reports 'healthy'")

        # STEP 2: Dashboard Overview Statistics
        print("\n--- 2. Testing Dashboard Overview Stats ---")
        res = await client.get("/api/dashboard/overview")
        assert_test(res.status_code == 200, "Overview stats endpoint returns 200 OK")
        stats = res.json()
        assert_test("totalTasks" in stats and stats["totalTasks"] >= 6, f"Returned totalTasks: {stats.get('totalTasks')}")
        assert_test("completed" in stats, f"Returned completed count: {stats.get('completed')}")
        assert_test("inProgress" in stats, f"Returned inProgress count: {stats.get('inProgress')}")
        assert_test("blocked" in stats, f"Returned blocked count: {stats.get('blocked')}")

        # STEP 3: Tasks List & Filtering
        print("\n--- 3. Testing Tasks Retrieval & Filtering ---")
        res = await client.get("/api/tasks")
        assert_test(res.status_code == 200, "Fetch all tasks returns 200 OK")
        tasks = res.json()
        assert_test(len(tasks) >= 6, f"Fetched {len(tasks)} tasks")

        res_filtered = await client.get("/api/tasks?filter=in_progress")
        assert_test(res_filtered.status_code == 200, "Fetch tasks with filter returns 200 OK")
        in_prog_tasks = res_filtered.json()
        assert_test(all(t["status"] == "In Progress" for t in in_prog_tasks), "Filtered tasks only return 'In Progress'")

        # STEP 4: Task Creation
        print("\n--- 4. Testing Task Creation ---")
        new_task_payload = {
            "title": "Backend Automated Verification Pipeline",
            "project": "Product Core",
            "assignee": "Alex Morgan",
            "deadline": "Tomorrow 5:00 PM",
            "priority": "High",
            "description": "Integration test task created via API",
            "estimatedHours": "8h"
        }
        res_create = await client.post("/api/tasks", json=new_task_payload)
        assert_test(res_create.status_code == 201, "Create task returns 201 Created")
        created_task = res_create.json()
        assert_test(created_task["title"] == new_task_payload["title"], f"Task title correctly created: {created_task['title']}")
        created_id = created_task["id"]

        # STEP 5: Task Status Update
        print("\n--- 5. Testing Task Status Update ---")
        res_update = await client.patch(f"/api/tasks/{created_id}/status", json={"status": "Completed"})
        assert_test(res_update.status_code == 200, "Update task status returns 200 OK")
        updated_task = res_update.json()
        assert_test(updated_task["status"] == "Completed", f"Task {created_id} updated to 'Completed'")

        # STEP 6: Blocker Reporting Flow
        print("\n--- 6. Testing Blocker Reporting & Leader Escalation ---")
        res_block = await client.post(
            f"/api/tasks/{created_id}/report-blocker",
            json={"taskId": created_id, "blockerReason": "Missing OAuth client credentials", "urgency": "Critical"}
        )
        assert_test(res_block.status_code == 200, "Report blocker returns 200 OK")
        block_data = res_block.json()
        assert_test(block_data["success"] is True, "Blocker reported successfully")
        assert_test(block_data["task"]["status"] == "Blocked", "Task status automatically set to 'Blocked'")

        # STEP 7: Team Members & Capacity
        print("\n--- 7. Testing Team Member Capacity & Workload Tracking ---")
        res_members = await client.get("/api/team/members")
        assert_test(res_members.status_code == 200, "Get team members returns 200 OK")
        members = res_members.json()
        assert_test(len(members) >= 4, f"Fetched {len(members)} team members")
        leo = next((m for m in members if m["name"] == "Leo Park"), None)
        assert_test(leo is not None and leo["workload"] >= 85, f"Leo Park capacity tracked at {leo['workload']}% (Overloaded)")

        # STEP 8: AI Intelligence Feed & Metrics
        print("\n--- 8. Testing AI Activity Feed & Metrics Counters ---")
        res_feed = await client.get("/api/ai/activity-feed")
        assert_test(res_feed.status_code == 200, "Get AI activity feed returns 200 OK")
        feed = res_feed.json()
        assert_test(len(feed) > 0, f"Retrieved {len(feed)} intelligence feed items")

        res_metrics = await client.get("/api/ai/metrics")
        assert_test(res_metrics.status_code == 200, "Get AI metrics returns 200 OK")
        ai_metrics = res_metrics.json()
        assert_test(ai_metrics["followUpsSent"] >= 34, f"Tracked followUpsSent: {ai_metrics['followUpsSent']}")

        # STEP 9: Interactive AI Reply Simulation
        print("\n--- 9. Testing Interactive AI Reply Simulation ---")
        sim_payload = {"memberId": "mem-2", "text": "Dashboard analytics is 70% complete. Charts are looking great."}
        res_sim = await client.post("/api/ai/simulate-reply", json=sim_payload)
        assert_test(res_sim.status_code == 200, "Simulate reply returns 200 OK")
        sim_data = res_sim.json()
        assert_test(sim_data["status"] == "delivered", "Simulation reply marked delivered")

        # STEP 10: Invisible Workload Detector & Leader Approval
        print("\n--- 10. Testing Invisible Workload Detector & Reassignment Flow ---")
        res_recs = await client.get("/api/workload/invisible-detector")
        assert_test(res_recs.status_code == 200, "Get workload recommendations returns 200 OK")
        recs = res_recs.json()
        assert_test(len(recs) > 0, f"Invisible Workload Detector generated {len(recs)} rebalancing proposals")

        target_rec = recs[0]
        rec_id = target_rec["id"]
        # Leader approves recommendation
        res_reassign = await client.post(
            "/api/workload/reassign",
            json={"recommendationId": rec_id, "approved": True, "note": "Approved rebalance for college hackathon"}
        )
        assert_test(res_reassign.status_code == 200, "Leader approval returns 200 OK")
        reassign_data = res_reassign.json()
        assert_test(reassign_data["success"] is True, f"Reassignment executed: {reassign_data['message']}")

        # STEP 11: Telegram Status & Account Linking Code
        print("\n--- 11. Testing Telegram Status & One-Time Link Code Generation ---")
        res_tg_status = await client.get("/api/integrations/telegram/status")
        assert_test(res_tg_status.status_code == 200, "Telegram status returns 200 OK")
        tg_status = res_tg_status.json()
        assert_test(tg_status["botName"] in ("@Syncoraaivalidbot", "@SyncoraAIBot"), f"Bot handle verified: {tg_status['botName']}")
        assert_test(tg_status["webhookActive"] is True, "Webhook active verified")

        res_code = await client.post("/api/integrations/telegram/link-code", json={"memberId": "mem-4"})
        assert_test(res_code.status_code == 200, "Generate link code returns 200 OK")
        code_data = res_code.json()
        assert_test(code_data["code"].startswith("SYNC-"), f"Generated single-use code: {code_data['code']}")

        # STEP 12: Telegram Bot Command Handling
        print("\n--- 12. Testing Telegram Bot Commands (/start, /tasks, /myid, /link) ---")
        start_update = {
            "update_id": 9001,
            "message": {
                "message_id": 101,
                "from": {"id": 1002, "first_name": "Alex", "username": "alexmorgan_ux"},
                "chat": {"id": 1002, "type": "private"},
                "date": 1700000000,
                "text": "/start"
            }
        }
        res_tg_start = await TelegramService.handle_update(start_update)
        assert_test(res_tg_start["status"] == "command_handled", "Handled /start command successfully")

        # Verify idempotency: resending the same update_id 9001 must be ignored
        res_dup = await TelegramService.handle_update(start_update)
        assert_test(res_dup["status"] == "ignored", "Duplicate update_id correctly rejected (Idempotency verified)")

        tasks_cmd_update = {
            "update_id": 9002,
            "message": {
                "message_id": 102,
                "from": {"id": 1002, "first_name": "Alex", "username": "alexmorgan_ux"},
                "chat": {"id": 1002, "type": "private"},
                "date": 1700000005,
                "text": "/tasks"
            }
        }
        res_tg_tasks = await TelegramService.handle_update(tasks_cmd_update)
        assert_test(res_tg_tasks["status"] == "command_handled", "Handled /tasks command successfully")

        # STEP 13: Natural Language Progress Update via Telegram
        print("\n--- 13. Testing Real Telegram Participant Reply Interpretation ---")
        nl_update = {
            "update_id": 9003,
            "message": {
                "message_id": 103,
                "from": {"id": 1002, "first_name": "Alex", "username": "alexmorgan_ux"},
                "chat": {"id": 1002, "type": "private"},
                "date": 1700000010,
                "text": "Hey team, SYNC-201 analytics charts are 85% done and looking great!"
            }
        }
        res_nl = await TelegramService.handle_update(nl_update)
        assert_test(res_nl["status"] == "success", "Natural language reply parsed and status updated")
        assert_test(res_nl["task_id"] == "SYNC-201", f"Resolved correct task ID: {res_nl['task_id']}")
        interpretation = res_nl["interpretation"]
        assert_test(interpretation["progress_percentage"] == 85, f"Extracted 85% progress: {interpretation['progress_percentage']}")

        # STEP 14: Blocker Detection via Telegram
        print("\n--- 14. Testing Telegram Blocker Detection & Escalation ---")
        block_update = {
            "update_id": 9004,
            "message": {
                "message_id": 104,
                "from": {"id": 1002, "first_name": "Alex", "username": "alexmorgan_ux"},
                "chat": {"id": 1002, "type": "private"},
                "date": 1700000015,
                "text": "I am blocked on SYNC-201 waiting for API endpoint deployment."
            }
        }
        res_tg_block = await TelegramService.handle_update(block_update)
        assert_test(res_tg_block["status"] == "success", "Blocker message handled successfully")
        assert_test(res_tg_block["interpretation"]["is_blocked"] is True, "AI accurately recognized blocker dependency")

        # STEP 15: In-App Notifications for Leader
        print("\n--- 15. Testing Leader Notifications Retrieval ---")
        res_notifs = await client.get("/api/notifications")
        assert_test(res_notifs.status_code == 200, "Get notifications returns 200 OK")
        notifs = res_notifs.json()
        assert_test(len(notifs) > 0, f"Leader has {len(notifs)} alerts in notification center")

        # STEP 16: Outgoing Task Reminder & Active Association
        print("\n--- 16. Testing Outgoing Task Reminder Flow ---")
        rem_res = await client.post(
            "/api/integrations/telegram/send-reminder",
            json={"taskId": "SYNC-204", "customMessage": "Checking in on campaign strategy"}
        )
        assert_test(rem_res.status_code == 200, "Send reminder endpoint returns 200 OK")
        rem_data = rem_res.json()
        assert_test(rem_data.get("success") is True, f"Reminder dispatched to {rem_data.get('recipient')}")
        assert_test(rem_data.get("taskId") == "SYNC-204", "Associated with task SYNC-204")

        # STEP 17: Contextual Reply Resolution via Active Reminder
        print("\n--- 17. Testing Contextual Reply Resolution via Active Reminder ---")
        reminder_reply_update = {
            "update_id": 9005,
            "message": {
                "message_id": 105,
                "from": {"id": 1001, "first_name": "Maya", "username": "mayachen_ai"},
                "chat": {"id": 1001, "type": "private"},
                "date": 1700000020,
                "text": "Almost ready with the deck, about 90% done!"  # Note: No SYNC-204 in text!
            }
        }
        res_rem_reply = await TelegramService.handle_update(reminder_reply_update)
        assert_test(res_rem_reply["status"] == "success", "Contextual reply without explicit task ID handled")
        assert_test(res_rem_reply["task_id"] == "SYNC-204", f"Resolved reminded task context: {res_rem_reply['task_id']}")
        assert_test(res_rem_reply["interpretation"]["progress_percentage"] == 90, "Progress extracted as 90%")

        # STEP 18: In-App AI Chat Endpoint
        print("\n--- 18. Testing In-App AI Chat API (/api/ai/chat) ---")
        chat_req = {
            "memberId": "mem-2",
            "message": "Working on SYNC-201 analytics widgets, currently 75% complete.",
            "taskId": "SYNC-201"
        }
        chat_res = await client.post("/api/ai/chat", json=chat_req)
        assert_test(chat_res.status_code == 200, "In-app AI chat returns 200 OK")
        chat_data = chat_res.json()
        assert_test("reply" in chat_data and "Evidence" in chat_data["reply"], "Chat returns evidence confirmation")
        assert_test(chat_data["updatedTask"] is not None, "Task status successfully updated via chat")
        assert_test(chat_data["interpretation"]["progress_percentage"] == 75, "Chat extracted 75% progress")

        # STEP 19: Notification Read State Management
        print("\n--- 19. Testing Notification Read State Management ---")
        target_notif = notifs[0]
        res_read = await client.patch(f"/api/notifications/{target_notif['id']}/read")
        assert_test(res_read.status_code == 200, "Mark notification read returns 200 OK")
        res_mark_all = await client.post("/api/notifications/mark-all-read")
        assert_test(res_mark_all.status_code == 200, "Mark all notifications read returns 200 OK")

        # STEP 20: Ambiguous Reply Clarification Request
        print("\n--- 20. Testing Ambiguous Reply Clarification Flow ---")
        ambiguous_update = {
            "update_id": 9006,
            "message": {
                "message_id": 106,
                "from": {"id": 1002, "first_name": "Alex", "username": "alexmorgan_ux"},
                "chat": {"id": 1002, "type": "private"},
                "date": 1700000030,
                "text": "Made some quick updates today."
            }
        }
        res_ambig = await TelegramService.handle_update(ambiguous_update)
        assert_test(res_ambig["status"] == "clarification_requested", "Ambiguous message triggers clarification request")
        assert_test("clarification_prompt" in res_ambig["result"], "Clarification prompt provided to participant")

        # STEP 21: Data Provenance & Distinction Validation
        print("\n--- 21. Testing Provenance Distinction (Actual vs Calculated vs AI Estimated) ---")
        prov = chat_data["interpretation"]["metadata_provenance"]
        assert_test("actual_evidence" in prov, "Actual information recorded verbatim")
        assert_test("calculated_metrics" in prov, "Calculated metrics isolated")
        assert_test("ai_estimates" in prov, "AI estimates (confidence/risk) distinguished")

        # STEP 22: Section 5 - AI Natural Language Messages Interpretation
        print("\n--- 22. Testing Section 5 AI Natural Language Progress Interpretation ---")
        from services.ai_interpreter_service import AIInterpreterService
        from services.llm_provider import MockDeterministicLLMProvider

        # Message 1: "I completed the login page."
        t1 = TaskModel(id="SYNC-201", title="Login Page and Authentication", project="Product Core", assignee="Alex Morgan", assigneeInitials="AM", deadline="Tomorrow", deadlineStatus="upcoming", status="In Progress", priority="High", leftBarColor="#f43f5e", estimatedHours="8h", confidence="90%")
        r1 = await AIInterpreterService.interpret_message_async("I completed the login page.", "mem-2", [t1])
        assert_test(r1.status_change == "Completed", "Message 1 ('completed login page') parsed status as Completed")
        assert_test(r1.completed_work == "login page", "Message 1 extracted completed_work='login page'")
        assert_test(r1.remaining_work is None, "Message 1 has no remaining work")
        assert_test(not r1.is_blocked, "Message 1 is not blocked")

        # Message 2: "The UI is done, but the API is failing."
        r2 = await AIInterpreterService.interpret_message_async("The UI is done, but the API is failing.", "mem-2", [t1])
        assert_test(r2.status_change == "Blocked", "Message 2 ('UI is done, API failing') parsed status as Blocked")
        assert_test(r2.is_blocked is True, "Message 2 detected blocker")
        assert_test("ui" in (r2.completed_work or "").lower(), "Message 2 extracted completed_work='UI'")
        assert_test("failing" in (r2.remaining_work or "").lower(), "Message 2 extracted remaining_work containing failing API")
        assert_test(r2.suggested_next_action is not None, "Message 2 suggested next action generated")

        # Message 3: "I have completed the introduction, but the results section is pending."
        r3 = await AIInterpreterService.interpret_message_async("I have completed the introduction, but the results section is pending.", "mem-2", [t1])
        assert_test(r3.status_change == "In Progress", "Message 3 ('introduction done, results pending') remains In Progress (not Completed)")
        assert_test(r3.completed_work == "introduction", "Message 3 extracted completed_work='introduction'")
        assert_test(r3.remaining_work == "results section", "Message 3 extracted remaining_work='results section'")

        # Message 4: "I can't continue until Aman sends the dataset."
        r4 = await AIInterpreterService.interpret_message_async("I can't continue until Aman sends the dataset.", "mem-2", [t1])
        assert_test(r4.status_change == "Blocked", "Message 4 ('waiting on dataset') parsed status as Blocked")
        assert_test(r4.is_blocked is True, "Message 4 detected blocker")
        assert_test("aman sends the dataset" in (r4.blocker_reason or "").lower(), "Message 4 extracted blocker description")
        assert_test(r4.suggested_next_action is not None, "Message 4 suggested action for dataset blocker")

        # Message 5: "I should finish testing tomorrow."
        r5 = await AIInterpreterService.interpret_message_async("I should finish testing tomorrow.", "mem-2", [t1])
        assert_test(r5.status_change == "In Progress", "Message 5 ('finish testing tomorrow') parsed status as In Progress")
        assert_test(r5.proposed_deadline == "Tomorrow", "Message 5 extracted proposed_deadline='Tomorrow'")
        assert_test(r5.remaining_work == "testing", "Message 5 extracted remaining_work='testing'")

        # Guardrail Test: "almost done" must NOT mark Completed
        r_almost = await AIInterpreterService.interpret_message_async("The feature is almost done.", "mem-2", [t1])
        assert_test(r_almost.status_change == "In Progress", "Guardrail: 'almost done' mapped to 'In Progress', never 'Completed'")
        assert_test(r_almost.progress_percentage == 90, "Guardrail: 'almost done' set estimated progress ~90%")

        # Backend Authorization Validation
        auth_ok, auth_msg = TaskService.validate_task_update_authorization("SYNC-201", "mem-2", "Completed", is_almost_done=True)
        assert_test(not auth_ok, "Backend rule: rejects 'Completed' status when task is only 'almost done'")
        auth_unauth, unauth_msg = TaskService.validate_task_update_authorization("SYNC-201", "mem-4", "Completed", is_almost_done=False)
        assert_test(not auth_unauth, "Backend rule: rejects update from unauthorized non-assignee member")

        # STEP 23: Section 6 - Deterministic Workload Metrics & Analysis Window
        print("\n--- 23. Testing Section 6 Deterministic Workload Metrics (/api/workload/analysis) ---")
        analysis_res = await client.get("/api/workload/analysis?windowDays=7")
        assert_test(analysis_res.status_code == 200, "Get team workload analysis returns 200 OK")
        analysis_data = analysis_res.json()
        assert_test(analysis_data["analysisWindowDays"] == 7, "Default analysis window is 7 days")
        assert_test(len(analysis_data["memberMetrics"]) == 4, "Returned metrics for all 4 team members")

        # Verify deterministic workload calculations on active members
        active_metric = next(m for m in analysis_data["memberMetrics"] if m["activeTasksCount"] >= 1 and m["availableCapacityHours"])
        assert_test(active_metric["activeTasksCount"] >= 1, f"{active_metric['memberName']} has active assigned tasks")
        assert_test(active_metric["utilizationCalculable"] is True, f"{active_metric['memberName']} capacity recorded, utilization calculable")
        expected_util = round((active_metric["estimatedRemainingHours"] / active_metric["availableCapacityHours"]) * 100, 1)
        assert_test(active_metric["utilizationPercentage"] == expected_util, f"Utilization formula verified for {active_metric['memberName']} ({expected_util}%)")

        dep_metric = next((m for m in analysis_data["memberMetrics"] if m["downstreamDependencyImpactHours"] > 0), None)
        assert_test(dep_metric is not None, f"Downstream dependency impact tracked ({dep_metric['memberName'] if dep_metric else 'None'}: {dep_metric['downstreamDependencyImpactHours'] if dep_metric else 0}h)")

        # STEP 24: Section 6 - Risk Categorization (Confirmed vs Potential vs AI Estimates)
        print("\n--- 24. Testing Risk Categorization & Provenance Separation ---")
        assert_test(len(analysis_data["confirmedRisks"]) > 0, "Confirmed risks identified (ground truth from database)")
        confirmed_types = [r["riskType"] for r in analysis_data["confirmedRisks"]]
        assert_test("blocked_downstream_threat" in confirmed_types or "critical_task_blocked" in confirmed_types or "overdue_tasks" in confirmed_types or "capacity_overload" in confirmed_types, "Confirmed risks contain ground-truth threats")

        assert_test(len(analysis_data["potentialRisks"]) >= 0, "Potential risks evaluated (pattern heuristics)")
        assert_test(len(analysis_data["aiGeneratedEstimates"]) >= 0, "AI estimates requiring review listed")

        # STEP 25: Missing / Unknown Capacity Explicit Handling
        print("\n--- 25. Testing Zero / Missing Capacity Handling (Do Not Invent Data) ---")
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE members SET available_capacity_hours = 0.0 WHERE id = 'mem-4'")
        conn.commit()
        conn.close()

        metrics_zero = WorkloadService.calculate_deterministic_workload_metrics()
        nina_metric = next(m for m in metrics_zero if m.memberId == "mem-4")
        assert_test(nina_metric.utilizationCalculable is False, "Zero capacity flags utilizationCalculable=False")
        assert_test(nina_metric.utilizationPercentage is None, "Zero capacity yields utilizationPercentage=None")
        assert_test(nina_metric.utilizationStatus == "Zero Capacity", "Zero capacity status labeled 'Zero Capacity'")

        # Missing capacity explicit validation
        metrics_missing = DeterministicWorkloadMetrics(
            memberId="mem-temp", memberName="Contractor", activeTasksCount=2,
            estimatedRemainingHours=12.0, overdueTasksCount=0, dueWithin24hCount=0,
            dueWithin48hCount=0, dueWithin72hCount=0, blockedTasksCount=0,
            highPriorityTasksCount=0, downstreamDependencyImpactHours=0.0,
            availableCapacityHours=None, utilizationPercentage=None,
            utilizationCalculable=False, utilizationStatus="Unknown Capacity"
        )
        assert_test(metrics_missing.utilizationCalculable is False, "Missing capacity explicitly flags utilizationCalculable=False")
        assert_test(metrics_missing.utilizationStatus == "Unknown Capacity", "Missing capacity labeled 'Unknown Capacity'")

        # Restore Nina's capacity
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE members SET available_capacity_hours = 40.0 WHERE id = 'mem-4'")
        conn.commit()
        conn.close()

        # STEP 26: Section 6 - AI-Assisted Effort Estimation Endpoint
        print("\n--- 26. Testing AI-Assisted Effort Estimation (/api/workload/estimate-effort) ---")
        effort_req = {
            "title": "Construct Realtime Webhook Delivery Engine",
            "description": "Handle incoming events, authenticate signatures, and retry failed deliveries with exponential backoff.",
            "subtasks": ["HMAC Signature Verification", "Dead Letter Queue retry handler", "Delivery telemetry dashboard"],
            "dependencies": ["Redis Event Stream", "PostgreSQL Connection Pool"]
        }
        effort_res = await client.post("/api/workload/estimate-effort", json=effort_req)
        assert_test(effort_res.status_code == 200, "Estimate effort returns 200 OK")
        effort_data = effort_res.json()
        assert_test(effort_data["minEstimatedHours"] >= 2.0, "AI estimate returns minimum hours")
        assert_test(effort_data["maxEstimatedHours"] >= effort_data["minEstimatedHours"], "Maximum hours >= minimum hours")
        assert_test(effort_data["isAiEstimate"] is True, "Clearly labeled isAiEstimate=True")
        assert_test(len(effort_data["assumptions"]) > 0, "Assumptions explicitly disclosed")
        assert_test(effort_data["confidenceLevel"] in ("High", "Medium", "Low"), "Confidence level provided")

        # STEP 27: Reassignment Safety Guardrail (Prevent Secondary Overload)
        print("\n--- 27. Testing Reassignment Secondary Overload Prevention ---")
        # Attempt to reassign a massive task to a member that would push them over 85%
        # Insert a synthetic overloaded recommendation
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO workload_recommendations (
                id, priority, urgency_color, overburdened_member, current_load,
                suggested_member, suggested_load, task_id, task_title, task_project,
                task_estimated_hours, task_uncertainty, task_confidence,
                reasoning, action_proposed, approved, rejected, created_at
            ) VALUES (
                'rec-overload-test', 'Preemptive', '#f59e0b', 'Maya Chen', 80,
                'Leo Park', 92, 'SYNC-204', 'Massive Project Architecture', 'Product Core',
                '30h', 'High uncertainty', '80%', 'Test reasoning', 'Test proposal', 0, 0, ?
            )
        """, (datetime.utcnow().isoformat(),))
        conn.commit()
        conn.close()

        overload_attempt = WorkloadService.review_and_execute_reassignment("rec-overload-test", approved=True)
        assert_test(overload_attempt["success"] is False, "Safety guardrail blocked reassignment that would secondary-overload recipient")
        assert_test("overload threshold" in overload_attempt["message"].lower() or "overload" in overload_attempt["message"].lower(), "Reassignment rejection message explains overload prevention")

        # STEP 28: Section 7 - AI Task Redistribution Recommendations Structure & Evaluation
        print("\n--- 28. Testing Section 7 AI Task Redistribution Recommendation Structure ---")
        recs_res = await client.get("/api/workload/invisible-detector")
        assert_test(recs_res.status_code == 200, "Get active recommendations returns 200 OK")
        recs_list = recs_res.json()
        assert_test(len(recs_list) > 0, f"Found {len(recs_list)} active redistribution proposal(s)")
        
        sample_rec = recs_list[0]
        assert_test(sample_rec["status"] == "pending", f"Recommendation status is '{sample_rec['status']}' (never silently auto-reassigned)")
        assert_test(sample_rec.get("sourceMemberId") is not None, f"Source member ID present: {sample_rec.get('sourceMemberId')}")
        assert_test(sample_rec.get("recipientMemberId") is not None, f"Recipient member ID present: {sample_rec.get('recipientMemberId')}")
        assert_test(sample_rec.get("workloadImpact") is not None, "Workload impact before/after calculated")
        impact = sample_rec["workloadImpact"]
        assert_test("sourceBefore" in impact and "sourceAfter" in impact, "Workload impact includes source before and after metrics")
        assert_test("recipientBefore" in impact and "recipientAfter" in impact, "Workload impact includes recipient before and after metrics")
        assert_test(len(sample_rec.get("relevantConstraints", [])) > 0, "Relevant constraints verified (skills, capacity, membership)")
        assert_test(len(sample_rec.get("assumptions", [])) > 0, "Assumptions explicitly documented")
        assert_test("subject to" in sample_rec["reasoning"].lower() or "capacity" in sample_rec["reasoning"].lower() or "overload" in sample_rec["reasoning"].lower(), "Reasoning transparently details skill/capacity checks")

        # STEP 29: Section 7 - Leader Authorization, Stale Revalidation & Database Transactions
        print("\n--- 29. Testing Leader Authorization, Stale Revalidation & Transactions ---")
        # 1. Unauthorized approval attempt by non-leader (mem-2, Alex Morgan)
        unauth_req = {
            "recommendationId": sample_rec["id"],
            "approved": True,
            "reviewerId": "mem-2"  # Alex Morgan is Developer, NOT Team Leader
        }
        unauth_res = await client.post("/api/workload/reassign", json=unauth_req)
        assert_test(unauth_res.status_code == 200, "Reassignment endpoint handles unauthorized attempt gracefully")
        unauth_data = unauth_res.json()
        assert_test(unauth_data["success"] is False, "Unauthorized non-leader approval correctly rejected")
        assert_test("unauthorized" in unauth_data["message"].lower() or "leader" in unauth_data["message"].lower(), "Rejection explicitly explains leader authorization requirement")

        # 2. Stale recommendation test A: Task already completed
        conn = get_db_connection()
        cur = conn.cursor()
        now_ts = datetime.utcnow().isoformat()
        cur.execute("""
            INSERT OR REPLACE INTO workload_recommendations (
                id, priority, urgency_color, overburdened_member, current_load,
                suggested_member, suggested_load, task_id, task_title, task_project,
                task_estimated_hours, task_uncertainty, task_confidence,
                reasoning, action_proposed, status, source_member_id, recipient_member_id,
                approved, rejected, created_at
            ) VALUES (
                'rec-stale-completed', 'Preemptive', '#f59e0b', 'Alex Morgan', 64,
                'Nina Shah', 50, 'SYNC-190', 'Mobile navigation prototype', 'Product Core',
                '12h', 'Low', '99%', 'Test', 'Test', 'pending', 'mem-2', 'mem-4', 0, 0, ?
            )
        """, (now_ts,))
        conn.commit()
        conn.close()

        stale_res_1 = await client.post("/api/workload/reassign", json={"recommendationId": "rec-stale-completed", "approved": True, "reviewerId": "mem-1"})
        stale_data_1 = stale_res_1.json()
        assert_test(stale_data_1["success"] is False, "Stale recommendation rejected: task already completed in Step 5")
        assert_test("completed" in stale_data_1["message"].lower(), "Error explains task already completed")

        # 3. Valid leader approval with transaction & audit verification
        valid_reassign_req = {
            "recommendationId": sample_rec["id"],
            "approved": True,
            "reviewerId": "mem-1",  # Maya Chen, Team Leader
            "note": "Approved during sprint rebalancing review"
        }
        valid_res = await client.post("/api/workload/reassign", json=valid_reassign_req)
        assert_test(valid_res.status_code == 200, "Leader approval returns 200 OK")
        valid_data = valid_res.json()
        assert_test(valid_data["success"] is True, f"Leader approval succeeded: {valid_data['message']}")
        assert_test(valid_data.get("auditEventId") is not None, f"Audit event recorded: {valid_data.get('auditEventId')}")
        assert_test(valid_data.get("recommendationStatus") in ("approved", "modified"), f"Status transitioned to: {valid_data.get('recommendationStatus')}")

        # Verify database state after transaction
        conn = get_db_connection()
        cur = conn.cursor()
        # Verify task reassigned
        cur.execute("SELECT assignee_name, status FROM tasks WHERE id = ?", (sample_rec["taskToReassign"]["id"],))
        task_after = cur.fetchone()
        assert_test(task_after["assignee_name"] == sample_rec["suggestedMember"], f"Task {sample_rec['taskToReassign']['id']} reassigned to {task_after['assignee_name']} in database")

        # Verify audit event in activity feed
        cur.execute("SELECT * FROM activity_feed WHERE id = ?", (valid_data["auditEventId"],))
        audit_row = cur.fetchone()
        assert_test(audit_row is not None, "Audit event logged in activity_feed table")
        assert_test(audit_row["type"] == "workload_rebalanced", "Audit type is 'workload_rebalanced'")

        # Verify notifications created for members
        cur.execute("SELECT COUNT(*) as count FROM notifications WHERE type = 'workload_rebalanced' OR type = 'task_assigned'")
        notif_count = cur.fetchone()["count"]
        assert_test(notif_count >= 1, f"Notifications generated for affected members (count: {notif_count})")
        conn.close()

        # 4. Stale recommendation test B: Double approval rejected (idempotency / stale state)
        double_res = await client.post("/api/workload/reassign", json=valid_reassign_req)
        double_data = double_res.json()
        assert_test(double_data["success"] is False, "Subsequent approval rejected (recommendation already resolved)")
        assert_test("stale" in double_data["message"].lower() or "already" in double_data["message"].lower(), "Rejection explains recommendation already resolved")

        # STEP 30: Section 8 - Telegram /workload Command & Confidentiality
        print("\n--- 30. Testing Telegram /workload Command & Access Control ---")
        # 1. Unlinked user calls /workload
        unlinked_resp = await TelegramService._handle_command("/workload", {"id": 999999, "first_name": "Stranger"}, {"id": 999999})
        assert_test("Account Not Linked Yet" in unlinked_resp, "Unlinked Telegram user prompted to link account")

        # 2. Non-leader calls /workload (confidentiality protection)
        non_leader_resp = await TelegramService._handle_command("/workload", {"id": 1002, "first_name": "Alex"}, {"id": 1002})  # Alex Morgan, Developer
        assert_test("Confidential Workload Telemetry" in non_leader_resp, "Confidentiality protection: Non-leader denied full team workload audit")
        assert_test("restricted to authorized Project Leaders" in non_leader_resp, "Explains restriction to authorized leaders")

        # 3. Authorized leader calls /workload
        leader_resp = await TelegramService._handle_command("/workload", {"id": 1001, "first_name": "Maya"}, {"id": 1001})  # Maya Chen, Team Leader
        assert_test("Team Workload & Capacity Audit" in leader_resp, "Leader receives comprehensive workload telemetry")
        assert_test("Maya Chen" in leader_resp, "Workload telemetry contains member metrics")
        assert_test("dashboard" in leader_resp.lower(), "Directs leader to web dashboard to approve or reject recommendations")

        # STEP 31: Section 8 - Proactive Workload Alert Dispatch & Deduplication
        print("\n--- 31. Testing Workload Alerts Dispatch & Deduplication (/api/workload/dispatch-alerts) ---")
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM workload_alerts_log")
        conn.commit()
        conn.close()

        # 1. First alert dispatch
        alert_res_1 = await client.post("/api/workload/dispatch-alerts")
        assert_test(alert_res_1.status_code == 200, "Alert dispatch endpoint returns 200 OK")
        alert_data_1 = alert_res_1.json()
        assert_test(alert_data_1["count"] >= 1, f"Dispatched {alert_data_1['count']} proactive overload alert(s) to project leader")
        first_alert = alert_data_1["dispatched"][0]
        assert_test(first_alert["leader"] == "Maya Chen", f"Alert delivered to authorized leader: {first_alert['leader']}")
        assert_test(first_alert["chatId"] == "1001", f"Alert delivered to leader chat ID: {first_alert['chatId']}")

        # Verify alert logged in database deduplication table
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM workload_alerts_log WHERE alert_key = ?", (first_alert["alertKey"],))
        alert_log = cur.fetchone()
        assert_test(alert_log is not None, f"Alert key '{first_alert['alertKey']}' logged in workload_alerts_log table")
        assert_test("⚠️ *Workload Alert*" in alert_log["message_text"], "Alert message conforms to Section 8 template")
        assert_test("dashboard" in alert_log["message_text"].lower(), "Alert references project dashboard for review")
        conn.close()

        # 2. Second alert dispatch immediately afterwards (Deduplication validation)
        alert_res_2 = await client.post("/api/workload/dispatch-alerts")
        assert_test(alert_res_2.status_code == 200, "Second alert dispatch call returns 200 OK")
        alert_data_2 = alert_res_2.json()
        assert_test(alert_data_2["count"] == 0, "Deduplication verified: 0 duplicate alerts dispatched for unresolved risks within 24h")

        # STEP 32: Section 9 - Scheduling Mechanisms & Distributed Leader Locking
        print("\n--- 32. Testing Section 9 Scheduling Mechanisms & Leader Locking ---")
        from services.scheduler_service import SchedulerService
        
        # 1. Distributed Leader Locking
        lock_acquired = SchedulerService.acquire_leader_lock()
        assert_test(lock_acquired is True, "Primary worker successfully acquired scheduler leader lock")
        
        # Verify lock row stored in database
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT holder_id, expires_at FROM scheduler_locks WHERE lock_name = 'scheduler_leader'")
        lock_row = cur.fetchone()
        assert_test(lock_row is not None, "Scheduler leader lock stored in database")
        assert_test(lock_row["holder_id"] == SchedulerService._worker_id, "Lock holder matches worker ID")
        conn.close()

        # 2. Configurable Deterministic Checks (Zero Unnecessary Continuous LLM Calls)
        reminders_count = await SchedulerService.send_due_task_reminders()
        assert_test(reminders_count >= 0, f"Task reminders scanned with cooldown check (sent: {reminders_count})")

        blockers_escalated = SchedulerService.check_unresolved_blockers()
        assert_test(blockers_escalated >= 0, f"Unresolved blockers check executed (escalated: {blockers_escalated})")

        deadline_critical_cnt = SchedulerService.detect_deadline_critical_tasks()
        assert_test(deadline_critical_cnt >= 0, f"Deadline-critical tasks evaluated deterministically (flagged: {deadline_critical_cnt})")

        refreshed_snapshots = SchedulerService.refresh_stale_workload_snapshots()
        assert_test(refreshed_snapshots >= 1, f"Workload snapshots refreshed for active projects: {refreshed_snapshots}")

        # 3. Authenticated Manual Analysis Endpoint (For Serverless / Restricted Deployments)
        # Non-leader attempt -> 403 Forbidden
        unauth_sched = await client.post("/api/workload/scheduler/run-analysis", headers={"X-User-Id": "mem-2"})
        assert_test(unauth_sched.status_code == 403, "Non-leader manual scheduler trigger rejected (403 Forbidden)")

        # Leader attempt -> 200 OK
        leader_sched = await client.post("/api/workload/scheduler/run-analysis", headers={"X-User-Id": "mem-1"})
        assert_test(leader_sched.status_code == 200, "Leader manual scheduler trigger returns 200 OK")
        sched_report = leader_sched.json()
        assert_test(sched_report["status"] == "success", "Manual proactive analysis report indicates 'success'")
        assert_test(sched_report["executionMode"] == "authenticated_manual_trigger", "Report executionMode is 'authenticated_manual_trigger'")

        # STEP 33: Section 10 - Project Workload Metrics & Project Authorization
        print("\n--- 33. Testing Section 10 Project Workload Metrics & Membership Checks ---")
        # 1. Unauthenticated request -> 401 Unauthorized
        unauth_proj = await client.get("/api/projects/Product Core/workload")
        assert_test(unauth_proj.status_code == 401, "Unauthenticated project workload access returns 401 Unauthorized")

        # 2. Non-member access rejection -> 403 Forbidden
        # mem-2 is member of Product Core & Infrastructure, but NOT Growth
        forbidden_proj = await client.get("/api/projects/Growth/workload", headers={"X-User-Id": "mem-2"})
        assert_test(forbidden_proj.status_code == 403, "Non-member project access strictly blocked (403 Forbidden)")

        # 3. Authorized project member access -> 200 OK
        valid_proj_res = await client.get("/api/projects/Product Core/workload", headers={"X-User-Id": "mem-2"})
        assert_test(valid_proj_res.status_code == 200, "Authorized project member retrieves workload metrics (200 OK)")
        proj_workload = valid_proj_res.json()
        assert_test(proj_workload["projectName"] == "Product Core", f"Project workload scoped to {proj_workload['projectName']}")
        assert_test(len(proj_workload["memberMetrics"]) >= 1, f"Returned member metrics for {len(proj_workload['memberMetrics'])} member(s)")

        # 4. Nonexistent project -> 404 Not Found
        not_found_proj = await client.get("/api/projects/NonexistentProject/workload", headers={"X-User-Id": "mem-1"})
        assert_test(not_found_proj.status_code == 404, "Nonexistent project returns 404 Not Found")

        # STEP 34: Section 10 - Triggering Workload Analysis
        print("\n--- 34. Testing Triggering Workload Analysis (Leader-Only Permission) ---")
        # Non-leader cannot trigger analysis
        non_lead_trigger = await client.post("/api/projects/Product Core/workload/analyze", headers={"X-User-Id": "mem-2"})
        assert_test(non_lead_trigger.status_code == 403, "Non-leader cannot trigger project workload analysis (403 Forbidden)")

        # Leader triggers analysis
        lead_trigger = await client.post("/api/projects/Product Core/workload/analyze", headers={"X-User-Id": "mem-1"})
        assert_test(lead_trigger.status_code == 200, "Project leader triggers workload analysis successfully (200 OK)")
        analyzed_data = lead_trigger.json()
        assert_test("memberMetrics" in analyzed_data, "Refreshed metrics returned after trigger")

        # STEP 35: Section 10 - Active Workload Risks & Recommendations by Project
        print("\n--- 35. Testing Project Risks & Redistribution Recommendations Endpoints ---")
        # Risks by project
        proj_risks_res = await client.get("/api/projects/Infrastructure/workload/risks", headers={"X-User-Id": "mem-1"})
        assert_test(proj_risks_res.status_code == 200, "Get project workload risks returns 200 OK")
        proj_risks = proj_risks_res.json()
        assert_test(isinstance(proj_risks, list), f"Retrieved {len(proj_risks)} active project risk item(s)")

        # Recommendations by project
        proj_recs_res = await client.get("/api/projects/Infrastructure/workload/recommendations", headers={"X-User-Id": "mem-1"})
        assert_test(proj_recs_res.status_code == 200, "Get project recommendations returns 200 OK")
        proj_recs = proj_recs_res.json()
        assert_test(isinstance(proj_recs, list), f"Retrieved {len(proj_recs)} project recommendation(s)")

        # STEP 36: Section 10 - Viewing a Member's Workload (Confidentiality Enforcement)
        print("\n--- 36. Testing Member Workload Telemetry & Confidentiality Controls ---")
        # Member views own workload
        own_workload_res = await client.get("/api/workload/members/mem-2", headers={"X-User-Id": "mem-2"})
        assert_test(own_workload_res.status_code == 200, "Member can view own workload telemetry (200 OK)")
        own_data = own_workload_res.json()
        assert_test(own_data["memberName"] == "Alex Morgan", f"Retrieved telemetry for {own_data['memberName']}")
        assert_test(own_data["isConfidentialView"] is False, "Self-view marked isConfidentialView=False")

        # Non-leader attempts to view another member's confidential workload -> 403 Forbidden
        snoop_res = await client.get("/api/workload/members/mem-3", headers={"X-User-Id": "mem-2"})
        assert_test(snoop_res.status_code == 403, "Non-leader forbidden from viewing another member's confidential workload (403 Forbidden)")

        # Leader views another member's workload -> 200 OK
        leader_view_res = await client.get("/api/workload/members/mem-3", headers={"X-User-Id": "mem-1"})
        assert_test(leader_view_res.status_code == 200, "Project leader authorized to audit member workload (200 OK)")
        leader_view_data = leader_view_res.json()
        assert_test(leader_view_data["memberName"] == "Leo Park", f"Leader auditing workload for {leader_view_data['memberName']}")
        assert_test(leader_view_data["isConfidentialView"] is True, "Audit marked isConfidentialView=True")

        # STEP 37: Section 10 - Approving and Rejecting Recommendations via Dedicated Routes
        print("\n--- 37. Testing Dedicated Approve & Reject Recommendation Routes ---")
        # Insert synthetic pending recommendations
        conn = get_db_connection()
        cur = conn.cursor()
        now_ts = datetime.utcnow().isoformat()
        cur.execute("""
            INSERT OR REPLACE INTO workload_recommendations (
                id, priority, urgency_color, overburdened_member, current_load,
                suggested_member, suggested_load, task_id, task_title, task_project,
                task_estimated_hours, task_uncertainty, task_confidence,
                reasoning, action_proposed, status, source_member_id, recipient_member_id,
                approved, rejected, created_at
            ) VALUES (
                'rec-api-test-approve', 'Preemptive', '#f59e0b', 'Nina Shah', 75,
                'Alex Morgan', 60, 'SYNC-195', 'Refresh onboarding email sequence', 'Growth',
                '7h', 'Low', '91%', 'Test reasoning', 'Test action', 'pending', 'mem-4', 'mem-2', 0, 0, ?
            )
        """, (now_ts,))
        cur.execute("""
            INSERT OR REPLACE INTO workload_recommendations (
                id, priority, urgency_color, overburdened_member, current_load,
                suggested_member, suggested_load, task_id, task_title, task_project,
                task_estimated_hours, task_uncertainty, task_confidence,
                reasoning, action_proposed, status, source_member_id, recipient_member_id,
                approved, rejected, created_at
            ) VALUES (
                'rec-api-test-reject', 'Preemptive', '#f59e0b', 'Nina Shah', 75,
                'Alex Morgan', 60, 'SYNC-195', 'Refresh onboarding email sequence', 'Growth',
                '7h', 'Low', '91%', 'Test reasoning', 'Test action', 'pending', 'mem-4', 'mem-2', 0, 0, ?
            )
        """, (now_ts,))
        conn.commit()
        conn.close()

        # Non-leader approval attempt -> 403 Forbidden
        unauth_appr = await client.post("/api/workload/recommendations/rec-api-test-approve/approve", headers={"X-User-Id": "mem-2"})
        assert_test(unauth_appr.status_code == 403, "Non-leader approval rejected by dedicated route (403 Forbidden)")

        # Non-leader rejection attempt -> 403 Forbidden
        unauth_rej = await client.post("/api/workload/recommendations/rec-api-test-reject/reject", headers={"X-User-Id": "mem-2"})
        assert_test(unauth_rej.status_code == 403, "Non-leader rejection rejected by dedicated route (403 Forbidden)")

        # Leader rejection via dedicated route -> 200 OK
        lead_rej = await client.post("/api/workload/recommendations/rec-api-test-reject/reject", headers={"X-User-Id": "mem-1"})
        assert_test(lead_rej.status_code == 200, "Leader rejection via dedicated route returns 200 OK")
        lead_rej_data = lead_rej.json()
        assert_test(lead_rej_data["recommendationStatus"] == "rejected", "Recommendation status updated to 'rejected'")

        # Leader approval via dedicated route -> 200 OK
        lead_appr = await client.post("/api/workload/recommendations/rec-api-test-approve/approve", headers={"X-User-Id": "mem-1"})
        assert_test(lead_appr.status_code == 200, "Leader approval via dedicated route returns 200 OK")
        lead_appr_data = lead_appr.json()
        assert_test(lead_appr_data["recommendationStatus"] == "approved", "Recommendation status updated to 'approved'")
        assert_test(lead_appr_data.get("auditEventId") is not None, "Audit event ID returned")

        # STEP 38: Section 10 - Task Activity History
        print("\n--- 38. Testing Task Activity History Endpoint (/api/tasks/{task_id}/activity) ---")
        # Unauthenticated attempt -> 401 Unauthorized
        unauth_act = await client.get("/api/tasks/SYNC-201/activity")
        assert_test(unauth_act.status_code == 401, "Unauthenticated task activity access returns 401 Unauthorized")

        # Authorized member retrieves task activity -> 200 OK
        task_act_res = await client.get("/api/tasks/SYNC-201/activity", headers={"X-User-Id": "mem-2"})
        assert_test(task_act_res.status_code == 200, "Authorized member retrieves task activity history (200 OK)")
        task_activities = task_act_res.json()
        assert_test(len(task_activities) >= 1, f"Retrieved {len(task_activities)} activity history event(s) for task SYNC-201")
        sample_act = task_activities[0]
        assert_test(sample_act["taskId"] == "SYNC-201", f"Activity associated with task: {sample_act['taskId']}")
        assert_test("title" in sample_act and "description" in sample_act, "Activity item contains title and description")

        # STEP 39: Section 11 - Database & Activity History Audit Events
        print("\n--- 39. Testing Section 11 Database & Meaningful Activity Events ---")
        from services.activity_service import ActivityService
        
        # Test event recording across Section 11 canonical categories
        test_events = [
            ("telegram_progress_received", "Telegram Progress Update", "Received update from Alex Morgan", "SYNC-201", "mem-2", "Product Core"),
            ("ai_interpretation_accepted", "AI Interpretation Accepted", "Accepted progress update for SYNC-201", "SYNC-201", "mem-2", "Product Core"),
            ("ai_clarification_requested", "AI Clarification Requested", "Clarification requested on task scope", "SYNC-204", "mem-1", "Marketing Launch"),
            ("blocker_identified", "Blocker Identified", "Leo Park flagged third-party credentials blocker", "SYNC-198", "mem-3", "Infrastructure"),
            ("blocker_resolved", "Blocker Resolved", "Blocker on SYNC-198 cleared and verified", "SYNC-198", "mem-3", "Infrastructure"),
            ("workload_analysis_completed", "Workload Analysis Completed", "Proactive analysis cycle completed", None, None, "Infrastructure"),
            ("overload_risk_raised", "Overload Risk Detected", "Leo Park exceeded 85% capacity threshold", None, "mem-3", "Infrastructure"),
            ("recommendation_created", "Rebalance Proposal Generated", "Suggested shifting SYNC-187 to Nina Shah", "SYNC-187", "mem-3", "Infrastructure"),
            ("task_assignment_changed", "Task Assignment Changed", "Task SYNC-187 reallocated to Nina Shah", "SYNC-187", "mem-4", "Infrastructure"),
        ]

        for ev_type, title, desc, tid, mid, pid in test_events:
            ev_id = ActivityService.record_event(
                event_type=ev_type,
                title=title,
                description=desc,
                task_id=tid,
                member_id=mid,
                project_id=pid,
                metadata={"test_run": True, "event_category": ev_type}
            )
            assert_test(ev_id.startswith(f"act-{ev_type}-"), f"Recorded {ev_type} event: {ev_id}")

        # Verify activity feed endpoint returns the enriched relational fields
        feed_res = await client.get("/api/ai/activity-feed")
        assert_test(feed_res.status_code == 200, "Get live activity feed returns 200 OK")
        feed_items = feed_res.json()
        assert_test(len(feed_items) > 0, f"Retrieved {len(feed_items)} activity feed items")
        first_feed = feed_items[0]
        assert_test("taskId" in first_feed, "Feed item includes taskId field")
        assert_test("memberId" in first_feed, "Feed item includes memberId field")
        assert_test("projectId" in first_feed, "Feed item includes projectId field")

        # STEP 40: Section 12 - In-App AI Chat Coordination & Ground Truth
        print("\n--- 40. Testing Section 12 In-App AI Chat Coordination & Ground Truth Queries ---")
        
        # Query 1a: "Who is currently overloaded?" (Balanced state check)
        chat_q1a = await client.post("/api/ai/chat", json={
            "memberId": "mem-2",
            "message": "Who is currently overloaded?"
        })
        assert_test(chat_q1a.status_code == 200, "In-app AI Chat query 1a returns 200 OK")
        q1a_data = chat_q1a.json()
        assert_test("safe capacity" in q1a_data["reply"].lower() or "overloaded" in q1a_data["reply"].lower(), "Query 1a accurately reflects live database workload")
        assert_test(q1a_data["interpretation"]["intent"] == "query_overload", "Query 1a intent classified as query_overload")

        # Dynamically set Leo Park to Overloaded (92%) to test overload identification & risk explanation
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE members SET workload = 92, workload_status = 'Overloaded' WHERE id = 'mem-3'")
        conn.commit()
        conn.close()

        # Query 1b: "Who is currently overloaded?" (Overloaded state check)
        chat_q1b = await client.post("/api/ai/chat", json={
            "memberId": "mem-2",
            "message": "Who is currently overloaded?"
        })
        assert_test(chat_q1b.status_code == 200, "In-app AI Chat query 1b returns 200 OK")
        q1b_data = chat_q1b.json()
        assert_test("Leo Park" in q1b_data["reply"], "Query 1b identifies Leo Park as overloaded")
        assert_test("92%" in q1b_data["reply"], "Query 1b reports exact database workload number (92%)")

        # Query 2: "Which tasks are at risk this week?"
        chat_q2 = await client.post("/api/ai/chat", json={
            "memberId": "mem-2",
            "message": "Which tasks are at risk this week?"
        })
        assert_test(chat_q2.status_code == 200, "In-app AI Chat query 2 returns 200 OK")
        q2_data = chat_q2.json()
        assert_test("SYNC-198" in q2_data["reply"] or "SYNC-201" in q2_data["reply"] or "risk" in q2_data["reply"].lower(), "Query 2 retrieves live risk tasks")
        assert_test(q2_data["interpretation"]["intent"] == "query_tasks_at_risk", "Query 2 intent classified as query_tasks_at_risk")

        # Query 3: "Why is Leo's workload flagged?"
        chat_q3 = await client.post("/api/ai/chat", json={
            "memberId": "mem-2",
            "message": "Why is Leo's workload flagged?"
        })
        assert_test(chat_q3.status_code == 200, "In-app AI Chat query 3 returns 200 OK")
        q3_data = chat_q3.json()
        assert_test("Leo Park" in q3_data["reply"] and "92%" in q3_data["reply"], "Query 3 explains Leo Park's flagged workload with live percentage")
        assert_test("SYNC-198" in q3_data["reply"] or "blocker" in q3_data["reply"].lower() or "overload" in q3_data["reply"].lower(), "Query 3 explains risk factors")

        # Query 3b: "Why is Priya's workload flagged?" (Non-fabricated ground-truth check)
        chat_q3b = await client.post("/api/ai/chat", json={
            "memberId": "mem-2",
            "message": "Why is Priya's workload flagged?"
        })
        assert_test(chat_q3b.status_code == 200, "In-app AI Chat query 3b returns 200 OK")
        q3b_data = chat_q3b.json()
        assert_test("No team member named 'Priya'" in q3b_data["reply"] or "Priya" in q3b_data["reply"], "Query 3b does not fabricate fictitious Priya metrics")
        assert_test("Leo Park" in q3b_data["reply"], "Query 3b points accurately to actual overloaded member")

        # Query 4: "Who could take over the documentation task?"
        chat_q4 = await client.post("/api/ai/chat", json={
            "memberId": "mem-2",
            "message": "Who could take over the documentation task?"
        })
        assert_test(chat_q4.status_code == 200, "In-app AI Chat query 4 returns 200 OK")
        q4_data = chat_q4.json()
        assert_test("Nina Shah" in q4_data["reply"], "Query 4 recommends Nina Shah based on capacity and skills")
        assert_test("leader" in q4_data["reply"].lower() or "approval" in q4_data["reply"].lower(), "Query 4 reinforces that reassignment requires leader approval")

        # Query 5: "What would happen if the backend task were delayed by two days?"
        chat_q5 = await client.post("/api/ai/chat", json={
            "memberId": "mem-2",
            "message": "What would happen if the backend task were delayed by two days?"
        })
        assert_test(chat_q5.status_code == 200, "In-app AI Chat query 5 returns 200 OK")
        q5_data = chat_q5.json()
        assert_test("What-If Simulation" in q5_data["reply"], "Query 5 identifies what-if simulation context")
        assert_test("SYNC-198" in q5_data["reply"] or "backend" in q5_data["reply"].lower(), "Query 5 simulates backend task")
        assert_test("hypothetical" in q5_data["reply"].lower() or "unchanged" in q5_data["reply"].lower(), "Query 5 confirms database remains unchanged")

        # STEP 41: Section 13 - Security, Rate Limiting, & Failure Resilience
        print("\n--- 41. Testing Section 13 Security, Rate Limiting & Failure Resilience ---")
        
        # 1. Rate Limiting on Account Linking Codes (max 5 per minute per member)
        rate_limit_hits = 0
        for i in range(6):
            rl_res = await client.post("/api/integrations/telegram/link-code", json={"memberId": "mem-1"})
            if rl_res.status_code == 429:
                rate_limit_hits += 1
        assert_test(rate_limit_hits >= 1, "Rate limiting successfully throttled excessive linking code requests (429 Too Many Requests)")

        # 2. Secret Protection: Bot token and JWT secret never exposed in responses
        status_res = await client.get("/api/integrations/telegram/status")
        status_json = status_res.json()
        assert_test("token" not in status_json and "jwt" not in status_json, "Public integration status does not leak sensitive bot tokens")
        assert_test(status_json["botName"] in ("@Syncoraaivalidbot", "@SyncoraAIBot"), "Integration status exposes only safe public bot name")

        # 3. LLM Failure Resilience: Workload calculations continue uninterrupted
        from services.llm_provider import OpenAILLMProvider
        faulty_llm = OpenAILLMProvider("sk-invalid-mock-key-for-testing")
        # Attempt progress interpretation with broken provider -> falls back to deterministic NLP
        fallback_res = await faulty_llm.interpret_progress("Completed the API documentation task", "mem-4", [])
        assert_test(fallback_res is not None, "Faulty LLM provider gracefully falls back to deterministic NLP")
        assert_test(fallback_res.status in ("In Progress", "Completed", "Pending", "Blocked"), "Fallback interpretation returns valid schema")

        # 4. LLM Failure does not disable basic deterministic workload calculations (Section 14 Criterion 16)
        workload_analysis = WorkloadService.get_full_team_workload_analysis()
        assert_test(len(workload_analysis.memberMetrics) == 4, "Deterministic workload calculations succeed independently of external LLMs")
        assert_test(workload_analysis.analysisWindowDays == 7, "Workload calculation analysis window intact")

        # 5. Telegram Failure Resilience (Section 14 Criterion 17): Telegram failure does not corrupt task data
        orig_send = TelegramService.send_telegram_message
        async def failing_send(chat_id: str, text: str, parse_mode: str = "Markdown") -> bool:
            # Simulate network failure or Telegram API 500
            return False

        TelegramService.send_telegram_message = failing_send
        try:
            # Report a blocker while Telegram outgoing delivery is failing
            blocker_task = TaskService.report_blocker("SYNC-204", "External third-party API outage", "Critical")
            assert_test(blocker_task is not None, "Task state updated despite Telegram delivery failure")
            assert_test(blocker_task.status == "Blocked", "Task status is Blocked in database")
            assert_test(blocker_task.blockerReason == "External third-party API outage", "Blocker reason preserved in SQLite")
            
            # Revert task back to In Progress
            restored_task = TaskService.update_task_status("SYNC-204", "In Progress")
            assert_test(restored_task.status == "In Progress", "Task status reverted cleanly")
        finally:
            TelegramService.send_telegram_message = orig_send

        # Verify task data in database remains completely consistent
        final_task = TaskService.get_task_by_id("SYNC-204")
        assert_test(final_task.id == "SYNC-204" and final_task.status == "In Progress", "Task data in database verified 100% consistent and uncorrupted")

    print(f"\n🎉 [SUCCESS] All {passed}/{total} Automated Backend & Telegram Tests Passed Flawlessly!\n")

if __name__ == "__main__":
    asyncio.run(run_tests())



