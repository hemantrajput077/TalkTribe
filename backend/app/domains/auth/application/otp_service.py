from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.auth.domain.otp_utils import generate_otp
from app.domains.auth.infrastructure.otp_repository import OtpRepository
from app.domains.auth.infrastructure.user_model import User
from app.domains.auth.infrastructure.user_repository import UserRepository
from app.infrastructure.config.config import settings


async def create_otp(db: AsyncSession, user_id: int, purpose: str = "REGISTER") -> str:
    otp_code = generate_otp(settings.OTP_LENGTH)
    expires_at = datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    otp_repo = OtpRepository(db)
    await otp_repo.create(user_id, otp_code, purpose, expires_at)
    return otp_code


async def verify_otp(
    db: AsyncSession, email: str, otp_code: str, purpose: str = "REGISTER"
) -> User:
    user_repo = UserRepository(db)
    otp_repo = OtpRepository(db)

    user = await user_repo.get_by_email(email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    otp_record = await otp_repo.get_valid(user.id, purpose)
    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid OTP found. Please request a new one.",
        )

    if otp_record.otp != otp_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")

    # Both mutations commit together to stay atomic — marking the OTP used
    # and activating the user must not be split across two transactions.
    otp_record.is_used = True
    user.is_verified = True
    await db.commit()
    await db.refresh(user)
    return user


async def expire_old_otps(db: AsyncSession, user_id: int, purpose: str = "REGISTER") -> None:
    otp_repo = OtpRepository(db)
    await otp_repo.expire_all(user_id, purpose)


async def resend_otp(db: AsyncSession, email: str) -> tuple[str, str]:
    user_repo = UserRepository(db)

    user = await user_repo.get_by_email(email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified"
        )

    await expire_old_otps(db, user.id, purpose="REGISTER")
    otp_code = await create_otp(db, user.id, purpose="REGISTER")
    return otp_code, user.username
