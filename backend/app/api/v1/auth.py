"""
Auth router — all authentication endpoints.

Endpoints:
  POST /auth/register        → create account
  POST /auth/login           → get access + refresh token
  POST /auth/refresh         → rotate refresh token
  POST /auth/logout          → revoke current refresh token
  POST /auth/logout-all      → revoke ALL tokens (all devices)
  GET  /auth/me              → return current user (protected)
  GET  /auth/user_data       → list all users (dev/admin only)
  DELETE /auth/users/{id}    → delete user
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.db.dependencies import get_db
from app.db.session import SessionLocal
from app.models.auth import User
from app.schemas.auth import CreateUser, RegisterResponse, UserLogin
from app.schemas.token import LogoutRequest, RefreshRequest, Token
from app.services.auth_service import (
    AuthService,
    get_auth_service,
    get_current_user,
)
from sqlalchemy import select

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Register ──────────────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account",
)
def register(
    body: CreateUser,
    svc: AuthService = Depends(get_auth_service),
):
    if svc.check_username_exist(body.username):
        raise HTTPException(status_code=400, detail="Username already exists.")
    if svc.check_email_exist(body.email):
        raise HTTPException(status_code=400, detail="Email already exists.")

    user = svc.create_user(
        username=body.username,
        email=body.email,
        password=body.password,
        full_name=body.full_name,
    )
    return user


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=Token,
    summary="Login and receive access + refresh tokens",
)
def login(
    body: UserLogin,
    svc: AuthService = Depends(get_auth_service),
):
    return svc.login(body.username, body.password)


# ── Refresh ───────────────────────────────────────────────────────────────────

@router.post(
    "/refresh",
    response_model=Token,
    summary="Rotate refresh token — returns a new token pair",
)
def refresh(
    body: RefreshRequest,
    svc: AuthService = Depends(get_auth_service),
):
    return svc.refresh_tokens(body.refresh_token)


# ── Logout ────────────────────────────────────────────────────────────────────

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke the current refresh token (single device logout)",
)
def logout(
    body: LogoutRequest,
    svc: AuthService = Depends(get_auth_service),
):
    svc.logout(body.refresh_token)


@router.post(
    "/logout-all",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke ALL refresh tokens for the current user (all devices)",
)
def logout_all(
    current_user: User = Depends(get_current_user),
    svc: AuthService = Depends(get_auth_service),
):
    svc.logout_all(current_user.id)


# ── Protected: current user ───────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=RegisterResponse,
    summary="Return the authenticated user's profile",
)
def me(current_user: User = Depends(get_current_user)):
    return current_user


# ── Admin / dev helpers ───────────────────────────────────────────────────────

@router.get("/user_data", summary="List all users (admin/dev)")
def user_data(db: SessionLocal = Depends(get_db)):
    users = db.execute(select(User)).scalars().all()
    if not users:
        return {"message": "No users found."}
    return users


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a user by ID",
)
def delete_user(
    user_id: int,
    db: SessionLocal = Depends(get_db),
):
    user = db.execute(
        select(User).where(User.id == user_id)
    ).scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    db.delete(user)
    db.commit()
    return {"success": True, "message": "User deleted successfully."}
