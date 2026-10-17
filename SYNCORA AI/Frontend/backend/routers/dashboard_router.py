"""
Syncora AI - Dashboard Overview Router
Endpoint: GET /api/dashboard/overview
"""

from fastapi import APIRouter
from models.schemas import OverviewStatsResponse
from services.project_summary_service import ProjectSummaryService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/overview", response_model=OverviewStatsResponse)
async def get_overview():
    """Returns top KPI numbers, sprint totals, and distribution metrics."""
    return ProjectSummaryService.get_overview_statistics()
