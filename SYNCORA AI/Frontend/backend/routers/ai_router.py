"""
Syncora AI - AI Activity and Intelligence Feed Router
Endpoints:
  GET  /api/ai/activity-feed
  GET  /api/ai/metrics
  POST /api/ai/simulate-reply
"""

from typing import List
from datetime import datetime
from fastapi import APIRouter
from database import get_db_connection
from models.schemas import (
    ActivityModel,
    AIMetricsModel,
    SimulateReplyRequest,
    SimulateReplyResponse,
    AIChatRequest,
    AIChatResponse,
)
from services.ai_interpreter_service import AIInterpreterService
from services.task_service import TaskService
from services.member_service import MemberService
from services.ai_chat_assistant_service import AIChatAssistantService
from services.activity_service import ActivityService

router = APIRouter(prefix="/ai", tags=["AI Intelligence"])

@router.get("/activity-feed", response_model=List[ActivityModel])
async def get_activity_feed():
    """Returns the live AI intelligence feed."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM activity_feed ORDER BY created_at DESC LIMIT 20")
    rows = cursor.fetchall()
    activities = [
        ActivityModel(
            id=r["id"],
            type=r["type"],
            icon=r["icon"],
            title=r["title"],
            description=r["description"],
            timeAgo=r["time_ago"],
            badgeText=r["badge_text"],
            badgeType=r["badge_type"],
            taskId=r["task_id"] if "task_id" in r.keys() else None,
            memberId=r["member_id"] if "member_id" in r.keys() else None,
            projectId=r["project_id"] if "project_id" in r.keys() else None,
            createdAt=r["created_at"] if "created_at" in r.keys() else None,
        )
        for r in rows
    ]
    conn.close()
    return activities

@router.get("/metrics", response_model=AIMetricsModel)
async def get_ai_metrics():
    """Returns real-time AI Activity Center counters."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ai_metrics WHERE id = 1")
    row = cursor.fetchone()
    conn.close()

    if row:
        return AIMetricsModel(
            followUpsSent=row["follow_ups_sent"],
            repliesReceived=row["replies_received"],
            blockersDetected=row["blockers_detected"],
            statusChanges=row["status_changes"],
            clarifications=row["clarifications"],
        )
    return AIMetricsModel(
        followUpsSent=34,
        repliesReceived=28,
        blockersDetected=7,
        statusChanges=19,
        clarifications=4,
    )

@router.post("/simulate-reply", response_model=SimulateReplyResponse)
async def simulate_reply(req: SimulateReplyRequest):
    """
    Simulates inbound Telegram message interpretation and pipeline progression
    for interactive demo and frontend telemetry.
    """
    text = req.text or "The analytics module is around 60% done. Charts are working; I'm validating the filters now."
    member_id = req.memberId or "mem-2"

    candidate_tasks = TaskService.get_tasks_for_member(member_id)
    ai_result = AIInterpreterService.interpret_message(text, member_id, candidate_tasks)

    # If task update was found, apply it after authorization validation
    if ai_result.task_id and ai_result.status_change:
        is_almost_done = any(p in text.lower() for p in ["almost done", "nearly done", "just wrapping up"])
        is_auth, auth_err = TaskService.validate_task_update_authorization(
            ai_result.task_id, member_id, ai_result.status_change, is_almost_done=is_almost_done
        )
        if is_auth:
            TaskService.update_task_status(
                ai_result.task_id,
                ai_result.status_change,
                note=ai_result.summary,
                completed_work=ai_result.completed_work,
                remaining_work=ai_result.remaining_work
            )

    return SimulateReplyResponse(
        step=4,
        status="delivered",
        message=f"Interpreted: {ai_result.summary} (Confidence: {ai_result.confidence}%)",
        timestamp=datetime.now().strftime("%I:%M %p")
    )

from services.ai_coordinator_service import AICoordinatorService

@router.post("/chat", response_model=AIChatResponse)
async def ai_chat(req: AIChatRequest):
    """
    Unified AI Coordinator Chat API.
    Used by the website chatbox and shared with the Telegram bot.
    Retrieves authorized task, deadline, blocker, and workload data from SQLite.
    """
    member_id = req.memberId or "mem-1"
    res = await AICoordinatorService.process_message(
        user_id=member_id,
        message=req.message,
        channel="website",
        task_id_context=req.taskId
    )
    return AIChatResponse(
        reply=res["reply"],
        interpretation=res["interpretation"],
        updatedTask=res.get("updatedTask"),
        blockerAlert=res.get("blockerAlert", False),
        timestamp=res["timestamp"]
    )

@router.get("/chat/history")
async def get_ai_chat_history(memberId: str = "mem-1"):
    """Returns conversation history for the specified user."""
    return AICoordinatorService.get_chat_history(memberId)

@router.delete("/chat/history")
async def clear_ai_chat_history(memberId: str = "mem-1"):
    """Clears conversation history for the specified user."""
    AICoordinatorService.clear_chat_history(memberId)
    return {"success": True, "message": "Conversation history cleared."}


