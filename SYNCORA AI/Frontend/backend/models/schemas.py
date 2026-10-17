"""
Syncora AI - Pydantic Request & Response Schemas
Defines structured contracts matching the frontend API service and Telegram bot updates.
"""

from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field

# ==============================================================================
# 1. Dashboard Overview Schemas
# ==============================================================================
class OverviewStatsResponse(BaseModel):
    totalTasks: int
    totalTasksSub: Optional[str] = "Across 3 projects"
    completed: int
    completedSub: Optional[str] = "44% completion rate"
    inProgress: int
    inProgressSub: Optional[str] = "5 due this week"
    pending: int
    pendingSub: Optional[str] = "2 unassigned"
    blocked: int
    blockedSub: Optional[str] = "3 need attention"
    trendRate: str = "+12%"

# ==============================================================================
# 2. Task Schemas
# ==============================================================================
class TaskModel(BaseModel):
    id: str
    title: str
    project: str
    assignee: str
    assigneeInitials: str
    assigneeBg: Optional[str] = "#18e5b4"
    assigneeTextColor: Optional[str] = "#090d16"
    deadline: str
    deadlineStatus: Optional[str] = "upcoming"
    status: str
    priority: str
    leftBarColor: Optional[str] = "#f59e0b"
    estimatedHours: Optional[str] = "8-12h"
    confidence: Optional[str] = "90%"
    blockerReason: Optional[str] = None
    description: Optional[str] = ""
    estimatedRemainingHours: Optional[float] = 8.0
    explicitEstimateHours: Optional[float] = None
    dependsOn: Optional[str] = ""
    deadlineDate: Optional[str] = None
    subtasks: Optional[List[str]] = Field(default_factory=list)
    completedWork: Optional[str] = None
    remainingWork: Optional[str] = None

class TaskCreateRequest(BaseModel):
    title: str
    project: Optional[str] = "Product Core"
    assignee: Optional[str] = "Maya Chen"
    deadline: Optional[str] = "Tomorrow"
    priority: Optional[str] = "High"
    description: Optional[str] = ""
    estimatedHours: Optional[str] = "6-10h"
    estimatedRemainingHours: Optional[float] = None
    dependsOn: Optional[str] = ""
    subtasks: Optional[List[str]] = None

class TaskStatusUpdateRequest(BaseModel):
    status: str
    note: Optional[str] = None
    completedWork: Optional[str] = None
    remainingWork: Optional[str] = None

class TaskBlockerReportRequest(BaseModel):
    taskId: Optional[str] = None
    blockerReason: str
    urgency: Optional[str] = "Critical"

class BlockerReportResponse(BaseModel):
    success: bool
    task: Optional[TaskModel] = None
    message: str

# ==============================================================================
# 3. Team Member Schemas
# ==============================================================================
class TeamMemberModel(BaseModel):
    id: str
    name: str
    initials: str
    role: str
    title: str
    avatarBg: Optional[str] = "#8b5cf6"
    avatarColor: Optional[str] = "#ffffff"
    online: bool = True
    activeTasks: int
    completionRate: int
    workload: int
    workloadStatus: str
    workloadColor: Optional[str] = "#18e5b4"
    email: str
    telegramHandle: Optional[str] = None
    telegramConnected: bool = False
    availableCapacityHours: Optional[float] = 35.0
    skills: Optional[str] = "General"
    phoneNumber: Optional[str] = None
    isPhoneVerified: bool = False
    phoneVerifiedAt: Optional[str] = None


# ==============================================================================
# 4. AI Activity & Metrics Schemas
# ==============================================================================
class ActivityModel(BaseModel):
    id: str
    type: str
    icon: str
    title: str
    description: str
    timeAgo: str
    badgeText: str
    badgeType: str
    taskId: Optional[str] = None
    memberId: Optional[str] = None
    projectId: Optional[str] = None
    createdAt: Optional[str] = None

class AIMetricsModel(BaseModel):
    followUpsSent: int
    repliesReceived: int
    blockersDetected: int
    statusChanges: int
    clarifications: int

class SimulateReplyRequest(BaseModel):
    memberId: Optional[str] = None
    text: Optional[str] = None

class SimulateReplyResponse(BaseModel):
    step: int
    status: str
    message: str
    timestamp: str

class AIChatRequest(BaseModel):
    memberId: Optional[str] = "mem-2"
    message: str
    taskId: Optional[str] = None

class AIChatResponse(BaseModel):
    reply: str
    interpretation: Dict[str, Any]
    updatedTask: Optional[TaskModel] = None
    blockerAlert: bool = False
    timestamp: str

# ==============================================================================
# 5. Workload Recommendations Schemas (Invisible Workload Detector)
# ==============================================================================
class WorkloadTaskDetail(BaseModel):
    id: str
    title: str
    project: str
    estimatedHours: str
    uncertainty: Optional[str] = None
    confidence: str

class WorkloadRecommendationModel(BaseModel):
    id: str
    priority: str
    urgencyColor: Optional[str] = "#f43f5e"
    overburdenedMember: str
    currentLoad: int
    suggestedMember: str
    suggestedLoad: int
    taskToReassign: WorkloadTaskDetail
    reasoning: str
    actionProposed: str
    status: str = "pending"
    sourceMemberId: Optional[str] = None
    recipientMemberId: Optional[str] = None
    workloadImpact: Optional[Dict[str, Any]] = None
    relevantConstraints: Optional[List[str]] = None
    confidence: Optional[str] = "88%"
    assumptions: Optional[List[str]] = None
    reviewedBy: Optional[str] = None
    reviewedAt: Optional[str] = None

class WorkloadReassignRequest(BaseModel):
    recommendationId: str
    approved: bool = True
    note: Optional[str] = None
    action: Optional[str] = None
    reviewerId: Optional[str] = "mem-1"
    modifiedRecipient: Optional[str] = None

class WorkloadReassignResponse(BaseModel):
    success: bool
    message: str
    updatedWorkload: Optional[Dict[str, Any]] = None
    auditEventId: Optional[str] = None
    recommendationStatus: Optional[str] = None

class DeterministicWorkloadMetrics(BaseModel):
    memberId: str
    memberName: str
    activeTasksCount: int
    estimatedRemainingHours: float
    overdueTasksCount: int
    dueWithin24hCount: int
    dueWithin48hCount: int
    dueWithin72hCount: int
    blockedTasksCount: int
    highPriorityTasksCount: int
    downstreamDependencyImpactHours: float
    availableCapacityHours: Optional[float] = None
    utilizationPercentage: Optional[float] = None
    utilizationCalculable: bool
    utilizationStatus: str

class WorkloadRiskItem(BaseModel):
    riskType: str
    severity: str
    classification: str
    memberId: str
    memberName: str
    taskIds: List[str]
    explanation: str
    metricsSupporting: Dict[str, Any]

class TeamWorkloadAnalysisResponse(BaseModel):
    analysisWindowDays: int
    memberMetrics: List[DeterministicWorkloadMetrics]
    confirmedRisks: List[WorkloadRiskItem]
    potentialRisks: List[WorkloadRiskItem]
    aiGeneratedEstimates: List[WorkloadRiskItem]
    recommendations: List[WorkloadRecommendationModel]
    equilibriumSummary: str

class TaskEffortEstimateRequest(BaseModel):
    taskId: Optional[str] = None
    title: str
    description: Optional[str] = ""
    subtasks: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None

class TaskEffortEstimateResponse(BaseModel):
    taskId: Optional[str] = None
    title: str
    minEstimatedHours: float
    maxEstimatedHours: float
    estimatedHoursDisplay: str
    assumptions: List[str]
    confidenceLevel: str
    informationNeeded: List[str]
    isAiEstimate: bool = True


# ==============================================================================
# 6. Telegram Integration Schemas
# ==============================================================================
class TelegramStatusResponse(BaseModel):
    botName: str
    botStatus: str
    webhookActive: bool
    linkedGroup: str
    lastPing: str
    eventsHandledToday: int

class TelegramLinkCodeRequest(BaseModel):
    memberId: str

class TelegramLinkCodeResponse(BaseModel):
    code: str
    memberId: str
    expiresAt: str
    instructions: str

class TelegramLinkVerifyRequest(BaseModel):
    code: str
    telegramUserId: str
    telegramChatId: str
    telegramHandle: Optional[str] = None

class TelegramSimulateMessageRequest(BaseModel):
    telegramUserId: Optional[str] = "1002"
    text: str

class TelegramSendReminderRequest(BaseModel):
    taskId: str
    customMessage: Optional[str] = None

# Telegram incoming webhook format
class TelegramUser(BaseModel):
    id: int
    is_bot: Optional[bool] = False
    first_name: Optional[str] = None
    username: Optional[str] = None

class TelegramChat(BaseModel):
    id: int
    type: Optional[str] = "private"
    title: Optional[str] = None

class TelegramMessage(BaseModel):
    message_id: int
    from_user: Optional[TelegramUser] = Field(None, alias="from")
    chat: TelegramChat
    date: Optional[int] = None
    text: Optional[str] = None

class TelegramWebhookPayload(BaseModel):
    update_id: int
    message: Optional[TelegramMessage] = None

# ==============================================================================
# 7. Authentication Schemas
# ==============================================================================
class LoginRequest(BaseModel):
    email: str
    password: str
    role: Optional[str] = "leader"
    workspace: Optional[str] = "Nova Studio"

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: Optional[str] = "Team Member"
    title: Optional[str] = None
    workspace: Optional[str] = "Nova Studio"

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    email: str
    resetToken: str
    newPassword: str

class UserProfile(BaseModel):
    id: str
    name: str
    email: str
    role: str
    title: str
    workspace: str
    phoneNumber: Optional[str] = None
    isPhoneVerified: bool = False
    phoneVerifiedAt: Optional[str] = None
    telegramConnected: bool = False
    telegramHandle: Optional[str] = None
    telegramUserId: Optional[str] = None
    skills: Optional[str] = None
    availableCapacityHours: Optional[float] = 35.0
    avatarBg: Optional[str] = "#8b5cf6"
    avatarColor: Optional[str] = "#ffffff"

class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    skills: Optional[str] = None
    availableCapacityHours: Optional[float] = None
    avatarBg: Optional[str] = None
    avatarColor: Optional[str] = None

class LoginResponse(BaseModel):
    token: str
    user: UserProfile
    message: Optional[str] = "Authentication successful"

# ==============================================================================
# 7b. Phone Number OTP Verification Schemas
# ==============================================================================
class PhoneOtpSendRequest(BaseModel):
    phoneNumber: str
    countryCode: Optional[str] = "+91"

class PhoneOtpSendResponse(BaseModel):
    success: bool
    phoneNumber: str
    message: str
    expiresInSeconds: int = 300
    provider: str
    isDemoSandbox: bool = False
    sandboxOtp: Optional[str] = None  # Clearly disclosed development convenience only

class PhoneOtpVerifyRequest(BaseModel):
    phoneNumber: str
    otp: str

class PhoneOtpVerifyResponse(BaseModel):
    success: bool
    verified: bool
    phoneNumber: str
    message: str
    verifiedAt: Optional[str] = None

class PhoneStatusResponse(BaseModel):
    phoneNumber: Optional[str] = None
    isVerified: bool = False
    verifiedAt: Optional[str] = None
    provider: str
    providerConfigured: bool

class PhoneChangeRequest(BaseModel):
    newPhoneNumber: Optional[str] = None

# ==============================================================================
# 7c. Telegram Account Linking Token Schemas
# ==============================================================================
class TelegramLinkTokenResponse(BaseModel):
    token: str
    deepLink: str
    botUsername: str
    expiresAt: str
    instructions: str

class TelegramDisconnectResponse(BaseModel):
    success: bool
    message: str

# ==============================================================================
# 7d. Unified AI Chat Messages History Schemas
# ==============================================================================
class AIChatHistoryItem(BaseModel):
    id: str
    role: str  # "user" | "assistant"
    content: str
    channel: str = "website"
    timestamp: str

# ==============================================================================
# 8. Notification Schemas
# ==============================================================================
class NotificationModel(BaseModel):
    id: str
    recipientId: Optional[str] = None
    type: str
    title: str
    message: str
    urgency: str
    isRead: bool
    createdAt: str

# ==============================================================================
# 9. Project & Activity History Schemas (Sections 9 & 10)
# ==============================================================================
class ProjectModel(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    createdAt: str

class ProjectWorkloadResponse(BaseModel):
    projectId: str
    projectName: str
    memberMetrics: List[DeterministicWorkloadMetrics]
    confirmedRisks: List[WorkloadRiskItem]
    potentialRisks: List[WorkloadRiskItem]
    recommendations: List[WorkloadRecommendationModel]
    equilibriumSummary: str

class MemberWorkloadResponse(BaseModel):
    memberId: str
    memberName: str
    role: str
    metrics: DeterministicWorkloadMetrics
    assignedTasks: List[TaskModel]
    isConfidentialView: bool = False

class TaskActivityItem(BaseModel):
    id: str
    taskId: Optional[str] = None
    type: str
    icon: str
    title: str
    description: str
    timeAgo: str
    badgeText: str
    badgeType: str
    createdAt: str

class SchedulerRunReport(BaseModel):
    status: str
    timestamp: str
    remindersSent: int
    unresolvedBlockersChecked: int
    deadlineCriticalDetected: int
    staleSnapshotsRefreshed: int
    leaderAlertsDispatched: int
    meaningfulChangesDetected: bool
    executionMode: str = "manual_override"

