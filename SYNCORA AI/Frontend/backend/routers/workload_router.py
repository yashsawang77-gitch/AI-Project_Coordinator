"""
Syncora AI - Invisible Workload Detector Router
Endpoints:
  GET  /api/workload/invisible-detector  - Active task rebalancing proposals
  POST /api/workload/reassign            - Human-in-the-loop reassignment execution
  GET  /api/workload/analysis            - Complete 7-day deterministic metrics & risk audit
  POST /api/workload/estimate-effort     - AI-assisted effort estimation with disclosures
"""

from typing import List, Optional
from fastapi import APIRouter, Query, Header, HTTPException
from models.schemas import (
    WorkloadRecommendationModel,
    WorkloadReassignRequest,
    WorkloadReassignResponse,
    TeamWorkloadAnalysisResponse,
    TaskEffortEstimateRequest,
    TaskEffortEstimateResponse,
    MemberWorkloadResponse,
    SchedulerRunReport,
)
from services.workload_service import WorkloadService
from services.auth_service import AuthService, get_current_user

router = APIRouter(prefix="/workload", tags=["Invisible Workload Detector"])

@router.get("/invisible-detector", response_model=List[WorkloadRecommendationModel])
async def get_workload_recommendations():
    """Returns AI recommendations for redistributing tasks from overloaded members."""
    WorkloadService.analyze_team_workload_and_generate_recommendations()
    return WorkloadService.get_active_recommendations()

@router.post("/reassign", response_model=WorkloadReassignResponse)
async def review_reassignment(req: WorkloadReassignRequest):
    """
    Executes a task reassignment following explicit leader approval.
    Does NOT auto-reassign tasks without leader confirmation.
    Enforces safety guardrail against secondary overload of the recipient.
    Revalidates stale recommendations, records audit trail, and notifies members.
    """
    result = WorkloadService.review_and_execute_reassignment(
        recommendation_id=req.recommendationId,
        approved=req.approved,
        note=req.note,
        reviewer_id=req.reviewerId or "mem-1",
        modified_recipient=req.modifiedRecipient
    )
    return WorkloadReassignResponse(
        success=result["success"],
        message=result["message"],
        updatedWorkload=result.get("updatedWorkload"),
        auditEventId=result.get("auditEventId"),
        recommendationStatus=result.get("recommendationStatus"),
    )

@router.post("/dispatch-alerts")
async def dispatch_workload_alerts():
    """
    Evaluates detected overload risks and notifies authorized project leaders via Telegram.
    Enforces deduplication (no duplicate alerts for unresolved risks within 24h).
    """
    dispatched = await WorkloadService.dispatch_leader_workload_alerts()
    return {"dispatched": dispatched, "count": len(dispatched)}


@router.get("/analysis", response_model=TeamWorkloadAnalysisResponse)
async def get_team_workload_analysis(
    windowDays: int = Query(7, ge=1, le=30, description="Analysis window in days (default 7)")
):
    """
    Computes deterministic per-member workload calculations, classifies confirmed vs
    potential vs AI-generated risks, and assesses sprint equilibrium.
    """
    return WorkloadService.get_full_team_workload_analysis(analysis_window_days=windowDays)

@router.post("/estimate-effort", response_model=TaskEffortEstimateResponse)
async def estimate_task_effort(req: TaskEffortEstimateRequest):
    """
    AI-assisted effort estimation for tasks lacking explicit estimates.
    Returns minimum and maximum hours, assumptions, confidence level, and needed info.
    """
    return await WorkloadService.estimate_task_effort(req)

@router.post("/recommendations/{recommendation_id}/approve", response_model=WorkloadReassignResponse)
async def approve_recommendation_endpoint(
    recommendation_id: str,
    note: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
):
    """
    Approves a task redistribution recommendation (Section 10).
    Enforces authentication and strict Project Leader authorization.
    Never trusts client-supplied identity.
    """
    user = await get_current_user(authorization, x_user_id)
    if user["role"] != "Team Leader":
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Only an authorized Project Leader may approve task redistribution recommendations."
        )

    result = WorkloadService.review_and_execute_reassignment(
        recommendation_id=recommendation_id,
        approved=True,
        note=note,
        reviewer_id=user["id"]
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return WorkloadReassignResponse(
        success=result["success"],
        message=result["message"],
        updatedWorkload=result.get("updatedWorkload"),
        auditEventId=result.get("auditEventId"),
        recommendationStatus=result.get("recommendationStatus"),
    )

@router.post("/recommendations/{recommendation_id}/reject", response_model=WorkloadReassignResponse)
async def reject_recommendation_endpoint(
    recommendation_id: str,
    note: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
):
    """
    Rejects a task redistribution recommendation (Section 10).
    Enforces authentication and strict Project Leader authorization.
    """
    user = await get_current_user(authorization, x_user_id)
    if user["role"] != "Team Leader":
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Only an authorized Project Leader may reject task redistribution recommendations."
        )

    result = WorkloadService.review_and_execute_reassignment(
        recommendation_id=recommendation_id,
        approved=False,
        note=note,
        reviewer_id=user["id"]
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return WorkloadReassignResponse(
        success=result["success"],
        message=result["message"],
        updatedWorkload=result.get("updatedWorkload"),
        auditEventId=result.get("auditEventId"),
        recommendationStatus=result.get("recommendationStatus"),
    )

@router.get("/members/{member_id}", response_model=MemberWorkloadResponse)
async def get_member_workload(
    member_id: str,
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
):
    """
    Viewing a member's workload (Section 10).
    Enforces authentication and confidentiality:
    - Member may view their own workload.
    - Project Leader may view any member's workload.
    - Non-leaders are blocked from viewing other members' workload telemetry.
    """
    user = await get_current_user(authorization, x_user_id)
    AuthService.verify_member_workload_access(user, member_id)
    is_confidential = (user["id"] != member_id and user["role"] == "Team Leader")
    return WorkloadService.get_member_workload_detail(member_id, is_confidential_view=is_confidential)

@router.post("/scheduler/run-analysis", response_model=SchedulerRunReport)
async def trigger_manual_scheduler_analysis(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
):
    """
    Authenticated Manual Proactive Analysis Trigger (Section 9):
    If scheduled background jobs cannot run in the current deployment (e.g. serverless
    or restricted worker environments), this endpoint executes a full analysis cycle on demand.
    Enforces authentication and Project Leader authorization.
    """
    from services.scheduler_service import SchedulerService
    user = await get_current_user(authorization, x_user_id)
    if user["role"] != "Team Leader":
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Only an authorized Project Leader may trigger manual proactive analysis."
        )
    return await SchedulerService.run_proactive_analysis_cycle(execution_mode="authenticated_manual_trigger")

