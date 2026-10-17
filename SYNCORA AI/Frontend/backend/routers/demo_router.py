"""
Syncora AI - Demo Mode & Controlled Reset Router
Provides endpoints to inspect demo personas, reset to pristine demo state,
and verify the end-to-end hackathon presentation walkthrough.
"""

from fastapi import APIRouter
from database import init_db, get_db_connection

router = APIRouter(prefix="/demo", tags=["Demo Mode"])

@router.post("/reset")
async def reset_demo_data():
    """
    Safely resets database to pristine demo state with:
      - 1 Team Leader: Maya Chen (mem-1)
      - 3 Team Members: Alex Morgan (mem-2), Leo Park (mem-3), Nina Shah (mem-4)
      - Varied task statuses (In Progress, Completed, Blocked, Pending)
      - Overdue Task: SYNC-198 (Resolve payment webhook errors)
      - Unresolved Blocker: Third-party sandbox credentials
      - Workload imbalance: Leo Park (92% Overloaded), Nina Shah (46% Available)
    """
    init_db(force_reseed=True)
    return {
        "success": True,
        "message": "Demo workspace successfully reset to pristine hackathon state.",
        "personas": [
            {"id": "mem-1", "name": "Maya Chen", "role": "Team Leader", "email": "maya.chen@novastudio.ai"},
            {"id": "mem-2", "name": "Alex Morgan", "role": "Team Member", "email": "alex.m@novastudio.ai"},
            {"id": "mem-3", "name": "Leo Park", "role": "Team Member", "email": "leo.park@novastudio.ai"},
            {"id": "mem-4", "name": "Nina Shah", "role": "Team Member", "email": "nina.shah@novastudio.ai"},
        ]
    }

@router.get("/state")
async def get_demo_state():
    """Returns current demo overview for hackathon presentation."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, role, email, phone_number, is_phone_verified, telegram_connected, workload FROM members")
    members = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT id, title, status, priority, deadline, deadline_status, blocker_reason, assignee_name FROM tasks")
    tasks = [dict(r) for r in cursor.fetchall()]
    conn.close()

    overdue = [t for t in tasks if t.get("deadline_status") == "overdue" or "overdue" in (t.get("deadline") or "").lower()]
    blocked = [t for t in tasks if t.get("status") == "Blocked"]

    return {
        "workspace": "Nova Studio (Hackathon Demo)",
        "members": members,
        "totalTasks": len(tasks),
        "overdueTasks": overdue,
        "blockedTasks": blocked,
        "walkthroughSteps": [
            "1. Sign in as Team Leader (Maya Chen)",
            "2. Open Team Leader Dashboard (/overview)",
            "3. Assign a task to demo member (Alex Morgan)",
            "4. Observe task notification in Alex's Telegram chat",
            "5. Send /mytasks to Telegram bot to view assigned work",
            "6. Mark a task complete from Telegram (/mytasks -> Complete)",
            "7. Observe updated task status on the website",
            "8. Report a blocker through Telegram (/blocker)",
            "9. Observe blocker on website dashboard",
            "10. Open website AI chatbox",
            "11. Ask 'Which tasks are overdue?'",
            "12. Observe grounded answer citing SYNC-198 from database"
        ]
    }
