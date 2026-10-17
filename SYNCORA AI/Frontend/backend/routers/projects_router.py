"""
Syncora AI - Projects & Workload Access Router (Section 10)
Provides project-scoped workload, risk, recommendation, and manual analysis endpoints.
Strictly enforces authentication, project membership, and role-based authorization on every route.
Never trusts client-supplied user IDs or project IDs without validation.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Header, Depends

from models.schemas import (
    ProjectModel,
    ProjectWorkloadResponse,
    WorkloadRiskItem,
    WorkloadRecommendationModel,
    MemberWorkloadResponse,
)
from services.auth_service import AuthService, get_current_user
from services.workload_service import WorkloadService
from services.activity_service import ActivityService
from database import get_db_connection

router = APIRouter(prefix="/projects", tags=["Projects & Workload API"])


@router.get("", response_model=List[ProjectModel])
async def list_projects(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
):
    """
    Lists projects accessible to the authenticated user.
    Leaders see all workspace projects; team members see their assigned projects.
    """
    user = await get_current_user(authorization, x_user_id)
    conn = get_db_connection()
    cursor = conn.cursor()

    if user["role"] == "Team Leader":
        cursor.execute("SELECT * FROM projects ORDER BY name ASC")
    else:
        cursor.execute("""
            SELECT p.* FROM projects p
            JOIN project_members pm ON p.id = pm.project_id
            WHERE pm.member_id = ?
            ORDER BY p.name ASC
        """, (user["id"],))
    
    rows = cursor.fetchall()
    conn.close()

    return [
        ProjectModel(
            id=r["id"],
            name=r["name"],
            description=r["description"] or "",
            createdAt=r["created_at"]
        ) for r in rows
    ]


@router.get("/{project_id}/workload", response_model=ProjectWorkloadResponse)
async def get_project_workload(
    project_id: str,
    windowDays: int = Query(7, ge=1, le=30),
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
):
    """
    Retrieving project workload metrics (Section 10).
    Enforces authentication and project membership verification.
    """
    user = await get_current_user(authorization, x_user_id)
    project_row = AuthService.verify_project_access(user, project_id, require_leader=False)
    return WorkloadService.get_project_workload_analysis(project_row["name"], analysis_window_days=windowDays)


@router.post("/{project_id}/workload/analyze", response_model=ProjectWorkloadResponse)
async def trigger_project_workload_analysis(
    project_id: str,
    windowDays: int = Query(7, ge=1, le=30),
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
):
    """
    Triggering workload analysis (Section 10).
    Enforces authentication and strict Project Leader authorization.
    Re-runs deterministic analysis and refreshes cached snapshots.
    """
    user = await get_current_user(authorization, x_user_id)
    project_row = AuthService.verify_project_access(user, project_id, require_leader=True)
    
    # Re-run analysis and generate fresh proposals
    WorkloadService.analyze_team_workload_and_generate_recommendations()
    
    ActivityService.record_event(
        "workload_analysis_completed",
        "Workload Analysis Completed",
        f"Leader {user.get('name', 'Leader')} triggered workload analysis for project '{project_row['name']}'.",
        project_id=project_row["name"],
        member_id=user.get("id"),
        metadata={"windowDays": windowDays}
    )

    return WorkloadService.get_project_workload_analysis(project_row["name"], analysis_window_days=windowDays)


@router.get("/{project_id}/workload/risks", response_model=List[WorkloadRiskItem])
async def list_project_workload_risks(
    project_id: str,
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
):
    """
    Listing active workload risks for a project (Section 10).
    Enforces authentication and project membership.
    """
    user = await get_current_user(authorization, x_user_id)
    project_row = AuthService.verify_project_access(user, project_id, require_leader=False)
    analysis = WorkloadService.get_project_workload_analysis(project_row["name"])
    
    # Leaders see all confirmed and potential risks; members see non-confidential risks
    if user["role"] == "Team Leader":
        return analysis.confirmedRisks + analysis.potentialRisks
    else:
        # Member only sees risks affecting themselves or general tasks
        return [r for r in (analysis.confirmedRisks + analysis.potentialRisks) if r.memberId == user["id"]]


@router.get("/{project_id}/workload/recommendations", response_model=List[WorkloadRecommendationModel])
async def list_project_recommendations(
    project_id: str,
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
):
    """
    Retrieving redistribution recommendations for a project (Section 10).
    Enforces authentication and project membership.
    """
    user = await get_current_user(authorization, x_user_id)
    project_row = AuthService.verify_project_access(user, project_id, require_leader=False)
    analysis = WorkloadService.get_project_workload_analysis(project_row["name"])
    return analysis.recommendations


@router.get("/{project_id}/members/{member_id}/workload", response_model=MemberWorkloadResponse)
async def get_project_member_workload(
    project_id: str,
    member_id: str,
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
):
    """
    Viewing a member's workload within a project (Section 10).
    Enforces authentication, project membership, and confidentiality:
    - Member may view their own workload telemetry.
    - Project Leader may view any project member's workload telemetry.
    - Unauthorized non-leader access to another member's telemetry is rejected.
    """
    user = await get_current_user(authorization, x_user_id)
    project_row = AuthService.verify_project_access(user, project_id, require_leader=False)
    AuthService.verify_member_workload_access(user, member_id, project_id)
    
    is_confidential = (user["id"] != member_id and user["role"] == "Team Leader")
    return WorkloadService.get_member_workload_detail(member_id, is_confidential_view=is_confidential)
