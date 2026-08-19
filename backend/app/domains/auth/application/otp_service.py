from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.config.config import settings
from app.domains.auth.infrastructure.user_model import User
from app.domains.auth.infrastructure.otp_model import Otp
from app.domains.auth.domain.otp_utils import generate_otp


async def create_otp(db: AsyncSession, user_id: int, purpose: str = "REGISTER") -> str:
    otp_code = generate_otp(settings.OTP_LENGTH)
    expires_at = datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

    otp_record = Otp(
        user_id=user_id,
        otp=otp_code,
        purpose=purpose,
        expires_at=expires_at,
        is_used=False,
    )
    db.add(otp_record)
    await db.commit()
    await db.refresh(otp_record)
    return otp_code


async def verify_otp(
    db: AsyncSession, email: str, otp_code: str, purpose: str = "REGISTER"
) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    result = await db.execute(
        select(Otp)
        .where(
            and_(
                Otp.user_id == user.id,
                Otp.purpose == purpose,
                Otp.is_used == False,  # noqa: E712
                Otp.expires_at > datetime.utcnow(),
            )
        )
        .order_by(Otp.created_at.desc())
    )
    otp_record = result.scalar_one_or_none()

    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid OTP found. Please request a new one.",
        )

    if otp_record.otp != otp_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")

    otp_record.is_used = True
    user.is_verified = True
    await db.commit()
    await db.refresh(user)
    return user


async def expire_old_otps(db: AsyncSession, user_id: int, purpose: str = "REGISTER") -> None:
    result = await db.execute(
        select(Otp).where(
            and_(
                Otp.user_id == user_id,
                Otp.purpose == purpose,
                Otp.is_used == False,  # noqa: E712
            )
        )
    )
    for otp in result.scalars().all():
        otp.is_used = True
    await db.commit()


async def resend_otp(db: AsyncSession, email: str) -> tuple[str, str]:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.is_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified")

    await expire_old_otps(db, user.id, purpose="REGISTER")
    otp_code = await create_otp(db, user.id, purpose="REGISTER")
    return otp_code, user.username
