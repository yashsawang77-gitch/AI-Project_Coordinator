"""
Syncora AI - Team Router
Endpoint: GET /api/team/members
"""

from typing import List
from fastapi import APIRouter
from models.schemas import TeamMemberModel
from services.member_service import MemberService

router = APIRouter(prefix="/team", tags=["Team"])

@router.get("/members", response_model=List[TeamMemberModel])
async def get_team_members():
    """Returns team member list with verified capacity and Telegram connection state."""
    return MemberService.get_all_members()
