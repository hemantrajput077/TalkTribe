"""
Auth router — all authentication endpoints.

Endpoints:
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
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.dependencies import get_db
from app.models.auth import User
from app.schemas.auth import CreateUser, RegisterResponse, UserLogin
from app.schemas.otp import OTPResponse, ResendOTPRequest, VerifyEmailRequest
from app.schemas.token import LogoutRequest, RefreshRequest, Token
from app.services.auth_service import AuthService, get_auth_service, get_current_user
from app.services.email_service import send_otp_email
from app.services.otp_service import create_otp, resend_otp, verify_otp

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Register ──────────────────────────────────────────────────────────────────


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
        raise HTTPException(status_code=400, detail="Username already exists.")
    if await svc.check_email_exist(body.email):
        raise HTTPException(status_code=400, detail="Email already exists.")

    user = await svc.create_user(
        username=body.username,
        email=body.email,
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


# ── Verify Email ──────────────────────────────────────────────────────────────


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


# ── Resend OTP ────────────────────────────────────────────────────────────────


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


# ── Login ─────────────────────────────────────────────────────────────────────


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


# ── Refresh ───────────────────────────────────────────────────────────────────


@router.post(
    "/refresh",
    response_model=Token,
    summary="Rotate refresh token — returns a new token pair",
)
async def refresh(
    body: RefreshRequest,
    svc: AuthService = Depends(get_auth_service),
):
    return await svc.refresh_tokens(body.refresh_token)


# ── Logout ────────────────────────────────────────────────────────────────────


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke the current refresh token (single device logout)",
)
async def logout(
    body: LogoutRequest,
    svc: AuthService = Depends(get_auth_service),
):
    await svc.logout(body.refresh_token)


@router.post(
    "/logout-all",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke ALL refresh tokens for the current user (all devices)",
)
async def logout_all(
    current_user: User = Depends(get_current_user),
    svc: AuthService = Depends(get_auth_service),
):
    await svc.logout_all(current_user.id)


# ── Protected: current user ───────────────────────────────────────────────────


@router.get(
    "/me",
    response_model=RegisterResponse,
    summary="Return the authenticated user's profile",
)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


# ── Admin / dev helpers ───────────────────────────────────────────────────────


@router.get("/user_data", summary="List all users (admin/dev)")
async def user_data(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    if not users:
        return {"message": "No users found."}
    return users


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a user by ID",
)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    await db.delete(user)
    await db.commit()
    return {"success": True, "message": "User deleted successfully."}
