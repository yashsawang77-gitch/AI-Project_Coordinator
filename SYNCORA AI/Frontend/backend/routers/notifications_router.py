"""
Syncora AI - Notifications Router
Endpoint: GET /api/notifications
"""

from typing import List, Optional
from fastapi import APIRouter, Query
from models.schemas import NotificationModel
from services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("", response_model=List[NotificationModel])
async def list_notifications(recipientId: Optional[str] = Query(None)):
    """Fetches in-app alerts and notifications for the user/leader."""
    return NotificationService.get_notifications(recipientId)

@router.patch("/{notif_id}/read")
async def mark_notification_read(notif_id: str):
    """Marks a single notification as read."""
    success = NotificationService.mark_as_read(notif_id)
    return {"success": success, "notificationId": notif_id}

@router.post("/mark-all-read")
async def mark_all_notifications_read(recipientId: Optional[str] = Query(None)):
    """Marks all notifications for a recipient as read."""
    count = NotificationService.mark_all_read(recipientId)
    return {"success": True, "count": count}

