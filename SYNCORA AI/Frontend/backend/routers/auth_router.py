"""
Syncora AI - Authentication & Phone Verification Router
Endpoints:
  POST  /api/auth/login
  POST  /api/auth/register
  POST  /api/auth/forgot-password
  POST  /api/auth/reset-password
  GET   /api/auth/me
  PATCH /api/auth/profile
  POST  /api/auth/phone/send-otp
  POST  /api/auth/phone/verify-otp
  POST  /api/auth/phone/change-number
  GET   /api/auth/phone/status
"""

from typing import Optional
from fastapi import APIRouter, Header, Depends, HTTPException
from models.schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserProfile,
    ProfileUpdateRequest,
    PhoneOtpSendRequest,
    PhoneOtpSendResponse,
    PhoneOtpVerifyRequest,
    PhoneOtpVerifyResponse,
    PhoneStatusResponse,
    PhoneChangeRequest,
)
from services.auth_service import AuthService, get_current_user
from services.sms_service import SMSService

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    """Authenticates user with username or email and password."""
    user, token = AuthService.authenticate_user(req.email, req.password, req.role)
    return LoginResponse(
        token=token,
        user=user,
        message=f"Welcome back, {user.name}!"
    )

@router.post("/register", response_model=LoginResponse, status_code=201)
async def register(req: RegisterRequest):
    """Registers a new user account with simple credentials."""
    user, token = AuthService.register_user(
        name=req.name,
        email=req.email,
        password=req.password,
        role=req.role or "Team Member",
        title=req.title,
        workspace=req.workspace or "Nova Studio"
    )
    return LoginResponse(
        token=token,
        user=user,
        message=f"Account created successfully for {user.name}!"
    )

@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    """Initiates password reset."""
    return AuthService.forgot_password(req.email)

@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest):
    """Resets password using valid reset token."""
    return AuthService.reset_password(req.email, req.resetToken, req.newPassword)

@router.get("/me", response_model=UserProfile)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Returns the authenticated user's active session profile."""
    return AuthService._row_to_profile(current_user)

@router.patch("/profile", response_model=UserProfile)
async def update_profile(
    req: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Updates optional profile details moved from the login screen."""
    return AuthService.update_profile(current_user["id"], req.model_dump(exclude_unset=True))

# ==============================================================================
# Phone Number OTP Verification Endpoints
# ==============================================================================
@router.post("/phone/send-otp", response_model=PhoneOtpSendResponse)
async def send_phone_otp(
    req: PhoneOtpSendRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Sends an OTP to the given phone number via configured SMS provider.
    Enforces rate limits and expires old OTPs.
    """
    return await SMSService.request_otp(
        member_id=current_user["id"],
        phone_number=req.phoneNumber,
        country_code=req.countryCode or "+91"
    )

@router.post("/phone/verify-otp", response_model=PhoneOtpVerifyResponse)
async def verify_phone_otp(
    req: PhoneOtpVerifyRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Validates submitted 6-digit OTP and marks phone number verified.
    """
    return await SMSService.verify_otp(
        member_id=current_user["id"],
        phone_number=req.phoneNumber,
        submitted_otp=req.otp
    )

@router.post("/phone/change-number")
async def change_phone_number(
    req: PhoneChangeRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Clears verification status when changing number, requiring re-verification.
    """
    return SMSService.change_phone_number(current_user["id"], req.newPhoneNumber)

@router.get("/phone/status", response_model=PhoneStatusResponse)
async def get_phone_status(current_user: dict = Depends(get_current_user)):
    """Returns phone verification state and active SMS provider."""
    return SMSService.get_status(current_user["id"])
