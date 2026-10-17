"""
Syncora AI - Task Management Router
Endpoints:
  GET   /api/tasks
  POST  /api/tasks
  PATCH /api/tasks/{id}/status
  POST  /api/tasks/{id}/report-blocker
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Header
from models.schemas import (
    TaskModel,
    TaskCreateRequest,
    TaskStatusUpdateRequest,
    TaskBlockerReportRequest,
    BlockerReportResponse,
    TaskActivityItem,
)
from services.task_service import TaskService
from services.auth_service import AuthService, get_current_user
from database import get_db_connection

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.get("", response_model=List[TaskModel])
async def list_tasks(filter: Optional[str] = Query(None, description="all, in_progress, pending, blocked, completed")):
    """Returns list of tasks matching the optional status filter."""
    return TaskService.get_all_tasks(filter)

@router.post("", response_model=TaskModel, status_code=201)
async def create_task(req: TaskCreateRequest):
    """Creates a new task in the shared database and updates capacity metrics."""
    return TaskService.create_task(req)

@router.patch("/{task_id}/status", response_model=TaskModel)
async def update_task_status(task_id: str, req: TaskStatusUpdateRequest):
    """Updates a task's status and recalibrates team member metrics."""
    updated = TaskService.update_task_status(task_id, req.status, req.note)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")
    return updated

@router.post("/{task_id}/report-blocker", response_model=BlockerReportResponse)
async def report_blocker(task_id: str, req: TaskBlockerReportRequest):
    """Flags a critical blocker on a task and triggers leader escalation."""
    updated = TaskService.report_blocker(task_id, req.blockerReason, req.urgency or "Critical")
    if not updated:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")
    return BlockerReportResponse(
        success=True,
        task=updated,
        message="Blocker reported and team alerted via Telegram bot."
    )

@router.get("/{task_id}/activity", response_model=List[TaskActivityItem])
async def get_task_activity_history(
    task_id: str,
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
):
    """
    Retrieves complete task activity history (Section 10).
    Enforces authentication and project membership verification.
    """
    user = await get_current_user(authorization, x_user_id)
    task = TaskService.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    
    # Check permissions: user must be project member or leader
    AuthService.verify_project_access(user, task.project)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM activity_feed 
        WHERE task_id = ? OR description LIKE ? OR title LIKE ?
        ORDER BY created_at DESC
    """, (task_id, f"%{task_id}%", f"%{task_id}%"))
    rows = cursor.fetchall()
    conn.close()

    items = [
        TaskActivityItem(
            id=r["id"],
            taskId=task_id,
            type=r["type"],
            icon=r["icon"],
            title=r["title"],
            description=r["description"],
            timeAgo=r["time_ago"],
            badgeText=r["badge_text"],
            badgeType=r["badge_type"],
            createdAt=r["created_at"]
        ) for r in rows
    ]
    return items

