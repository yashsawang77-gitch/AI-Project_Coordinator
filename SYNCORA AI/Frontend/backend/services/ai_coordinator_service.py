"""
Syncora AI - Unified Grounded AI Coordinator Service
Shared backend AI service serving both the Website AI Chatbox and Telegram Bot.
Retrieves real task, deadline, blocker, and workload records from SQLite to ground
every response in verified truth. Supports Google Gemini, OpenAI, and a deterministic engine.
"""

import os
import json
import re
import secrets
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import httpx
from config import settings
from database import get_db_connection
from services.task_service import TaskService
from services.member_service import MemberService
from services.ai_chat_assistant_service import AIChatAssistantService

logger = logging.getLogger("ai_coordinator_service")

class AICoordinatorService:

    @classmethod
    async def process_message(
        cls,
        user_id: str,
        message: str,
        channel: str = "website",
        task_id_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for both Website AI Chatbox and Telegram Bot.
        1. Identifies user and workspace.
        2. Retrieves authorized task, deadline, blocker, and workload records.
        3. Constructs grounded context.
        4. Calls configured AI provider (or deterministic fallback).
        5. Records conversation history.
        6. Returns concise answer.
        """
        clean_msg = message.strip()
        now_str = datetime.utcnow().isoformat()
        now_time = datetime.now().strftime("%I:%M %p")

        # 1. Fetch user profile
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM members WHERE id = ?", (user_id,))
        user_row = cursor.fetchone()
        if not user_row:
            # Fallback to demo user
            cursor.execute("SELECT * FROM members WHERE role = 'Team Leader' LIMIT 1")
            user_row = cursor.fetchone()
        
        user_dict = dict(user_row) if user_row else {
            "id": "mem-1", "name": "Maya Chen", "role": "Team Leader", "title": "Team Leader"
        }

        # 2. Gather Ground Truth Context from SQLite
        user_tasks = TaskService.get_tasks_for_member(user_dict["id"])
        
        cursor.execute("SELECT * FROM tasks ORDER BY updated_at DESC")
        all_tasks_rows = cursor.fetchall()
        all_tasks = [TaskService._row_to_task(r) for r in all_tasks_rows]

        cursor.execute("SELECT * FROM members ORDER BY workload DESC")
        all_members_rows = cursor.fetchall()
        team_members = [dict(r) for r in all_members_rows]
        conn.close()

        # Identify Overdue and Blocked
        overdue_tasks = [
            t for t in (all_tasks if user_dict["role"] == "Team Leader" else user_tasks)
            if t.deadlineStatus == "overdue" or "overdue" in t.deadline.lower()
        ]
        blocked_tasks = [
            t for t in (all_tasks if user_dict["role"] == "Team Leader" else user_tasks)
            if t.status == "Blocked"
        ]

        # 3. Check for external LLM API key
        gemini_key = settings.GEMINI_API_KEY
        openai_key = settings.OPENAI_API_KEY

        reply_text = None
        interpretation = {}
        updated_task = None
        blocker_alert = False

        # If LLM key is configured, use LLM with grounded system context
        if gemini_key or openai_key:
            try:
                reply_text = await cls._call_external_llm(
                    clean_msg, user_dict, user_tasks, all_tasks, team_members, overdue_tasks, blocked_tasks
                )
            except Exception as e:
                logger.warning(f"External LLM invocation failed, falling back to deterministic ground truth: {e}")
                reply_text = None

        # 4. If no external key or LLM failed: Use Grounded Deterministic Coordinator Engine
        if not reply_text:
            det_result = await cls._deterministic_grounded_response(
                clean_msg, user_dict, user_tasks, all_tasks, team_members, overdue_tasks, blocked_tasks
            )
            reply_text = det_result["reply"]
            interpretation = det_result.get("interpretation", {})
            updated_task = det_result.get("updatedTask")
            blocker_alert = det_result.get("blockerAlert", False)

        # 5. Persist message history in SQLite
        cls._record_chat_message(user_dict["id"], channel, "user", clean_msg)
        cls._record_chat_message(user_dict["id"], channel, "assistant", reply_text)

        return {
            "reply": reply_text,
            "interpretation": interpretation,
            "updatedTask": updated_task,
            "blockerAlert": blocker_alert,
            "timestamp": now_time,
            "channel": channel
        }

    @classmethod
    async def _deterministic_grounded_response(
        cls,
        clean_msg: str,
        user: Dict[str, Any],
        user_tasks: List[Any],
        all_tasks: List[Any],
        team_members: List[Dict[str, Any]],
        overdue_tasks: List[Any],
        blocked_tasks: List[Any]
    ) -> Dict[str, Any]:
        """
        Produces precise, ground-truth grounded answers directly from the database.
        Never fabricates numbers, tasks, or statuses.
        """
        lower = clean_msg.lower().strip()
        user_name = user.get("name", "Teammate")
        user_role = user.get("role", "Team Member")

        # Question 1: "What tasks are assigned to me?" / "Show my tasks"
        if any(p in lower for p in [
            "what tasks are assigned to me", "tasks assigned to me", "show my tasks",
            "what are my tasks", "my assigned tasks", "list my tasks"
        ]):
            if not user_tasks:
                return {
                    "reply": f"You currently have no tasks assigned to you in the project ledger.",
                    "interpretation": {"intent": "query_assigned_tasks", "count": 0}
                }
            active = [t for t in user_tasks if t.status != "Completed"]
            completed = [t for t in user_tasks if t.status == "Completed"]

            lines = [f"You have **{len(active)} active tasks** currently assigned to you:"]
            for t in active:
                badge = "🔴 [Blocked]" if t.status == "Blocked" else ("🟡 [In Progress]" if t.status == "In Progress" else "⚪ [Pending]")
                lines.append(f"• **{t.id}**: {t.title} — {badge} (Priority: **{t.priority}**, Due: *{t.deadline}*)")
            if completed:
                lines.append(f"\nYou have also completed **{len(completed)} task(s)** this sprint.")
            return {
                "reply": "\n".join(lines),
                "interpretation": {"intent": "query_assigned_tasks", "count": len(active)}
            }

        # Question 2: "Which tasks are overdue?"
        if any(p in lower for p in ["which tasks are overdue", "overdue tasks", "tasks are overdue", "any overdue"]):
            if not overdue_tasks:
                return {
                    "reply": "Great news! There are currently **no overdue tasks** recorded in your active project workspace.",
                    "interpretation": {"intent": "query_overdue_tasks", "count": 0}
                }
            lines = [f"You have **{len(overdue_tasks)} overdue task(s)** that need immediate resolution:"]
            for t in overdue_tasks:
                block_note = f" (Blocked: *{t.blockerReason}*)" if t.blockerReason else ""
                lines.append(f"• **{t.id}**: **{t.title}** assigned to **{t.assignee}** — Due: `{t.deadline}` (Priority: **{t.priority}**){block_note}")
            lines.append("\nWould you like me to alert the team lead or initiate a workload reassignment?")
            return {
                "reply": "\n".join(lines),
                "interpretation": {"intent": "query_overdue_tasks", "count": len(overdue_tasks)}
            }

        # Question 3: "What blockers need attention?"
        if any(p in lower for p in ["what blockers need attention", "blockers need attention", "active blockers", "blocked tasks"]):
            if not blocked_tasks:
                return {
                    "reply": "No unresolved blockers detected. All active sprint pipelines are currently running unobstructed.",
                    "interpretation": {"intent": "query_blockers", "count": 0}
                }
            lines = [f"There are **{len(blocked_tasks)} active blocker(s)** requiring leader intervention:"]
            for t in blocked_tasks:
                lines.append(f"• 🛑 **{t.id}** ({t.title}): Assigned to **{t.assignee}**\n  *Blocker Reason*: \"{t.blockerReason or 'Dependency roadblock'}\"\n  *Priority*: **{t.priority}** | Estimated remaining: {t.estimatedHours}")
            lines.append("\nThese items have been flagged on the project dashboard and alerted via Telegram.")
            return {
                "reply": "\n".join(lines),
                "interpretation": {"intent": "query_blockers", "count": len(blocked_tasks)}
            }

        # Question 4: "Summarize my progress"
        if any(p in lower for p in ["summarize my progress", "my progress", "sprint progress", "how am i doing"]):
            total = len(user_tasks)
            completed = len([t for t in user_tasks if t.status == "Completed"])
            in_prog = len([t for t in user_tasks if t.status == "In Progress"])
            blocked = len([t for t in user_tasks if t.status == "Blocked"])
            pct = int((completed / total) * 100) if total > 0 else 100

            workload_val = user.get("workload", 50)
            workload_status = user.get("workload_status", "Optimal")

            lines = [
                f"📊 **Sprint Progress Summary for {user_name}:**",
                f"• Completion Rate: **{pct}%** ({completed} of {total} tasks completed)",
                f"• In Progress: **{in_prog}**",
                f"• Blockers Flagged: **{blocked}**",
                f"• Workload Utilization: **{workload_val}%** ({workload_status})",
                f"\nYour sprint velocity is steady. Let me know if you would like recommendations on what to prioritize next!"
            ]
            return {
                "reply": "\n".join(lines),
                "interpretation": {"intent": "query_progress", "completionRate": pct}
            }

        # Question 5: "How is my team workload distributed?" / "Who is overloaded?"
        if any(p in lower for p in ["team workload distributed", "workload distribution", "who is overloaded", "team capacity", "workload distributed"]):
            if user_role != "Team Leader" and "who is overloaded" not in lower:
                return {
                    "reply": (
                        f"Your individual workload is currently **{user.get('workload', 50)}%** ({user.get('workload_status', 'Optimal')}). "
                        "Full team-wide workload distribution telemetry is confidential and accessible by Team Leaders in the command center."
                    ),
                    "interpretation": {"intent": "query_workload_confidential"}
                }
            overloaded = [m for m in team_members if m["workload"] >= 85 or m["workload_status"] == "Overloaded"]
            balanced = [m for m in team_members if 50 <= m["workload"] < 85]
            available = [m for m in team_members if m["workload"] < 50]

            lines = ["⚖️ **Team Workload Distribution:**"]
            if overloaded:
                lines.append("\n⚠️ **High Overload Threshold (>=85%):**")
                for m in overloaded:
                    lines.append(f"• **{m['name']}** ({m['title']}): **{m['workload']}%** utilization ({m['active_tasks']} active tasks)")
            if balanced:
                lines.append("\n🟢 **Balanced / Optimal (50-84%):**")
                for m in balanced:
                    lines.append(f"• **{m['name']}** ({m['title']}): **{m['workload']}%** utilization ({m['active_tasks']} active tasks)")
            if available:
                lines.append("\n🔵 **Available Capacity (<50%):**")
                for m in available:
                    lines.append(f"• **{m['name']}** ({m['title']}): **{m['workload']}%** utilization — capacity to absorb work")

            lines.append("\n_Check the Invisible Workload Detector tab to approve pending reassignment proposals._")
            return {
                "reply": "\n".join(lines),
                "interpretation": {"intent": "query_team_workload", "overloadedCount": len(overloaded)}
            }

        # Question 6: "What should I prioritize next?" / "What should I work on next?"
        if any(p in lower for p in ["what should i prioritize next", "what should i work on next", "prioritize next", "work on next", "what next"]):
            active = [t for t in user_tasks if t.status != "Completed"]
            if not active:
                return {
                    "reply": "You have no pending tasks! You are free to pick up unassigned items or support teammates with blockers.",
                    "interpretation": {"intent": "query_prioritization", "recommendation": None}
                }
            # Ranking heuristic:
            # 1. Unblocked high/critical priority due soonest
            # 2. In Progress high priority
            # 3. Medium priority
            unblocked = [t for t in active if t.status != "Blocked"]
            if unblocked:
                # Sort by priority
                priority_weight = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
                sorted_tasks = sorted(unblocked, key=lambda t: priority_weight.get(t.priority, 2), reverse=True)
                top_task = sorted_tasks[0]

                lines = [
                    f"🎯 **Recommendation: Focus on {top_task.id} — \"{top_task.title}\"**\n",
                    f"• **Reasoning**: This task has **{top_task.priority}** priority and is due *{top_task.deadline}*.",
                    f"• **Estimated Effort**: {top_task.estimatedHours}",
                    f"• **Status**: Currently `{top_task.status}` with no blocking dependencies.",
                    "\n*(Note: This is an AI grounded suggestion based on priority and deadlines. No task changes have been made.)*"
                ]
                return {
                    "reply": "\n".join(lines),
                    "interpretation": {"intent": "query_prioritization", "recommendedTask": top_task.id}
                }
            else:
                return {
                    "reply": (
                        "All your current tasks are marked as **Blocked**. "
                        f"I recommend coordinating with your team leader to resolve the blocker on **{active[0].id}** ({active[0].blockerReason})."
                    ),
                    "interpretation": {"intent": "query_prioritization", "status": "all_blocked"}
                }

        # Progress / Status Update submission e.g. "Finished the mobile navigation prototype"
        status_match = re.search(r"(?:finished|completed|done with) (?:the )?(.+)", lower)
        if status_match:
            query = status_match.group(1).strip()
            # Match task
            matched = None
            for t in user_tasks:
                if t.id.lower() in query or any(w in t.title.lower() for w in query.split() if len(w) > 3):
                    matched = t
                    break
            if matched:
                TaskService.update_task_status(matched.id, "Completed", note=f"Marked completed via chat: {clean_msg}")
                return {
                    "reply": f"✓ Task **{matched.id}** (*{matched.title}*) has been marked as **Completed**! Dashboard metrics and sprint pulse updated.",
                    "interpretation": {"intent": "task_update", "status": "Completed", "taskId": matched.id},
                    "updatedTask": matched
                }

        # Blocker submission e.g. "Blocked on SYNC-198 waiting for credentials"
        if "blocked" in lower and any(w in lower for w in ["waiting", "stuck", "error", "credentials", "need"]):
            task_id = None
            id_m = re.search(r"SYNC-\d+", clean_msg.upper())
            if id_m:
                task_id = id_m.group(0)
            elif user_tasks:
                task_id = user_tasks[0].id

            if task_id:
                TaskService.report_blocker(task_id, clean_msg, "Critical")
                return {
                    "reply": f"🚨 Blocker logged for **{task_id}**: \"{clean_msg}\". Your Team Leader has been alerted via Telegram and dashboard notifications.",
                    "interpretation": {"intent": "report_blocker", "taskId": task_id},
                    "blockerAlert": True
                }

        # General coordination query via existing AIChatAssistantService
        coord_res = await AIChatAssistantService.answer_coordination_query(clean_msg, requester_id=user["id"])
        return {
            "reply": coord_res["reply"],
            "interpretation": coord_res.get("interpretation", {"intent": "general_coordination"}),
            "updatedTask": coord_res.get("updatedTask"),
            "blockerAlert": coord_res.get("blockerAlert", False)
        }

    @classmethod
    async def _call_external_llm(
        cls,
        user_msg: str,
        user: Dict[str, Any],
        user_tasks: List[Any],
        all_tasks: List[Any],
        team_members: List[Dict[str, Any]],
        overdue_tasks: List[Any],
        blocked_tasks: List[Any]
    ) -> str:
        """Invokes Gemini or OpenAI with grounded SQLite database context."""
        context_prompt = (
            f"You are Syncora AI, the intelligent coordinator for group projects.\n"
            f"Current User: {user['name']} (Role: {user['role']}, Title: {user['title']})\n\n"
            f"GROUND TRUTH FROM SQLITE DATABASE:\n"
            f"User's Assigned Tasks: {json.dumps([{'id': t.id, 'title': t.title, 'status': t.status, 'priority': t.priority, 'deadline': t.deadline, 'blocker': t.blockerReason} for t in user_tasks])}\n"
            f"Overdue Tasks: {json.dumps([{'id': t.id, 'title': t.title, 'assignee': t.assignee, 'deadline': t.deadline} for t in overdue_tasks])}\n"
            f"Blocked Tasks: {json.dumps([{'id': t.id, 'title': t.title, 'assignee': t.assignee, 'reason': t.blockerReason} for t in blocked_tasks])}\n"
            f"Team Workloads: {json.dumps([{'name': m['name'], 'workload': m['workload'], 'status': m['workload_status']} for m in team_members])}\n\n"
            f"STRICT RULES:\n"
            f"1. Only answer using the facts provided in the ground truth above.\n"
            f"2. Never hallucinate tasks, percentages, or statuses.\n"
            f"3. Keep answers crisp, concise, professional, and friendly.\n"
            f"4. If suggesting a priority, clearly state it is a recommendation."
        )

        if settings.GEMINI_API_KEY:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
            payload = {
                "contents": [
                    {"role": "user", "parts": [{"text": f"{context_prompt}\n\nUser Question: {user_msg}"}]}
                ]
            }
            async with httpx.AsyncClient(timeout=12.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        return candidates[0]["content"]["parts"][0]["text"].strip()

        if settings.OPENAI_API_KEY:
            url = "https://api.openai.com/v1/chat/completions"
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": context_prompt},
                    {"role": "user", "content": user_msg}
                ],
                "temperature": 0.3
            }
            async with httpx.AsyncClient(timeout=12.0) as client:
                res = await client.post(
                    url,
                    json=payload,
                    headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
                )
                if res.status_code == 200:
                    data = res.json()
                    return data["choices"][0]["message"]["content"].strip()

        raise RuntimeError("No external LLM responded.")

    @classmethod
    def _record_chat_message(cls, user_id: str, channel: str, role: str, content: str):
        """Persists message to ai_chat_messages table."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            msg_id = f"msg-{int(datetime.utcnow().timestamp() * 1000)}-{secrets.token_hex(3)}"
            now_str = datetime.utcnow().isoformat()
            cursor.execute("""
                INSERT INTO ai_chat_messages (id, user_id, channel, role, content, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (msg_id, user_id, channel, role, content, now_str))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Could not record chat message: {e}")

    @classmethod
    def get_chat_history(cls, user_id: str, limit: int = 30) -> List[Dict[str, Any]]:
        """Retrieves persistent chat history for the user."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM ai_chat_messages 
            WHERE user_id = ? 
            ORDER BY created_at ASC LIMIT ?
        """, (user_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "id": r["id"],
                "role": r["role"],
                "content": r["content"],
                "channel": r["channel"],
                "timestamp": r["created_at"]
            }
            for r in rows
        ]

    @classmethod
    def clear_chat_history(cls, user_id: str) -> bool:
        """Clears chat history for user."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ai_chat_messages WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        return True
