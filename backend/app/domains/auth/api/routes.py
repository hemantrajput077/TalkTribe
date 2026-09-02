"""
Auth routes — all authentication endpoints.

  POST /auth/register        → create account + send OTP
  POST /auth/verify-email    → verify email with OTP
  POST /auth/resend-otp      → resend OTP to email
  POST /auth/login           → get access + refresh token
  POST /auth/refresh         → rotate refresh token
  POST /auth/logout          → revoke current refresh token
  POST /auth/logout-all      → revoke ALL tokens (all devices)
  GET  /auth/me              → return current user (protected)
  GET  /auth/user_data       → list all users (dev/admin only)
  DELETE /auth/users/{id}    → delete user
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_identity, require_admin
from app.domains.auth.application.auth_service import AuthService, get_auth_service
from app.domains.auth.application.otp_service import create_otp, resend_otp, verify_otp
from app.domains.auth.schemas.auth import CreateUser, RegisterResponse, UserLogin
from app.domains.auth.schemas.identity import AuthenticatedIdentity
from app.domains.auth.schemas.otp import OTPResponse, ResendOTPRequest, VerifyEmailRequest
from app.domains.auth.schemas.token import LogoutRequest, RefreshRequest, Token
from app.infrastructure.database.dependencies import (
    get_db,  # still needed by register, verify-email, resend-otp
)
from app.infrastructure.email.email_service import send_otp_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=OTPResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account and send OTP for verification",
)
async def register(
    body: CreateUser,
    db: AsyncSession = Depends(get_db),
    svc: AuthService = Depends(get_auth_service),
):
    if await svc.check_username_exist(body.username):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="USERNAME_ALREADY_EXISTS")
    if await svc.check_email_exist(body.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="EMAIL_ALREADY_EXISTS")
    if await svc.check_phone_number_exist(body.phone_number):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="PHONE_ALREADY_EXISTS")

    user = await svc.create_user(
        username=body.username,
        email=body.email,
        phone_number=body.phone_number,
        password=body.password,
        full_name=body.full_name,
    )

    otp_code = await create_otp(db, user.id, purpose="REGISTER")
    email_sent = await send_otp_email(user.email, otp_code, user.username)

    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try resending OTP.",
        )

    return OTPResponse(
        message=f"Registration successful! OTP sent to {user.email}. Please verify your email to login."
    )


@router.post(
    "/verify-email",
    response_model=OTPResponse,
    summary="Verify email address with OTP",
)
async def verify_email(
    body: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
):
    await verify_otp(db, body.email, body.otp, purpose="REGISTER")
    return OTPResponse(message="Email verified successfully! You can now login.")


@router.post(
    "/resend-otp",
    response_model=OTPResponse,
    summary="Resend OTP to email",
)
async def resend_otp_endpoint(
    body: ResendOTPRequest,
    db: AsyncSession = Depends(get_db),
):
    otp_code, username = await resend_otp(db, body.email)
    email_sent = await send_otp_email(body.email, otp_code, username)

    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again later.",
        )

    return OTPResponse(message=f"New OTP sent to {body.email}. Please check your inbox.")


@router.post(
    "/login",
    response_model=Token,
    summary="Login and receive access + refresh tokens",
)
async def login(
    body: UserLogin,
    svc: AuthService = Depends(get_auth_service),
):
    return await svc.login(body.username, body.password)


@router.post(
    "/refresh",
    response_model=Token,
    summary="Rotate refresh token — returns a new token pair",
)
async def refresh(
    body: RefreshRequest,
    svc: AuthService = Depends(get_auth_service),
):
    return await svc.refresh_tokens(body.refresh_token, body.access_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke the current refresh token (single device logout)",
)
async def logout(
    body: LogoutRequest,
    svc: AuthService = Depends(get_auth_service),
):
    await svc.logout(body.refresh_token, body.access_token)


@router.post(
    "/logout-all",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke ALL refresh tokens for the current user (all devices)",
)
async def logout_all(
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    svc: AuthService = Depends(get_auth_service),
):
    await svc.logout_all(identity.user_id)


@router.get(
    "/me",
    response_model=RegisterResponse,
    summary="Return the authenticated user's profile",
)
async def me(
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    svc: AuthService = Depends(get_auth_service),
):
    return await svc.get_user_by_id(identity.user_id)


@router.get("/user_data", summary="List all users (admin only)")
async def user_data(
    _: AuthenticatedIdentity = Depends(require_admin),
    svc: AuthService = Depends(get_auth_service),
):
    users = await svc.get_all_users()
    if not users:
        return {"message": "No users found."}
    return users


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a user by ID (admin only)",
)
async def delete_user(
    user_id: int,
    _: AuthenticatedIdentity = Depends(require_admin),
    svc: AuthService = Depends(get_auth_service),
):
    deleted = await svc.delete_user_by_id(user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return {"success": True, "message": "User deleted successfully."}
