from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, status

from app.models.otp import Otp
from app.models.auth import User
from app.utils.otp import generate_otp
from app.config import settings

"""
OTP Service - Business logic for OTP operations.

This service handles:
1. Creating OTP records
2. Validating OTP
3. Expiring old OTPs
4. Resending OTP

Why separate service layer?
- Reusable: Can be called from multiple routes
- Testable: Easy to unit test without HTTP
- Maintainable: Business logic separated from API logic
"""


async def create_otp(
    db: AsyncSession,
    user_id: int,
    purpose: str = "REGISTER"
) -> str:
    """
    Generate and store a new OTP for a user.

    Args:
        db: Database session
        user_id: User ID to associate OTP with
        purpose: Purpose of OTP (REGISTER, PASSWORD_RESET, etc.)

    Returns:
        Generated OTP string

    Process:
    1. Generate random 6-digit OTP
    2. Calculate expiry time (current time + 5 minutes)
    3. Store in database
    4. Return OTP (to be sent via email)
    """
    # Generate OTP
    otp_code = generate_otp(settings.OTP_LENGTH)

    # Calculate expiry time
    expires_at = datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

    # Create OTP record
    otp_record = Otp(
        user_id=user_id,
        otp=otp_code,
        purpose=purpose,
        expires_at=expires_at,
        is_used=False
    )

    db.add(otp_record)
    await db.commit()
    await db.refresh(otp_record)

    return otp_code


async def verify_otp(
    db: AsyncSession,
    email: str,
    otp_code: str,
    purpose: str = "REGISTER"
) -> User:
    """
    Verify OTP and mark user as verified.

    Args:
        db: Database session
        email: User's email
        otp_code: OTP to verify
        purpose: Purpose of OTP (REGISTER, PASSWORD_RESET, etc.)

    Returns:
        Verified User object

    Raises:
        HTTPException: If validation fails

    Validation checks:
    1. User exists
    2. OTP exists for this user and purpose
    3. OTP not expired
    4. OTP not already used
    5. OTP matches

    Why all these checks?
    - User exists: Can't verify non-existent user
    - OTP exists: Can't verify without OTP
    - Not expired: Security measure (limits brute force window)
    - Not used: Prevents OTP reuse attacks
    - Matches: Obviously needs to match
    """
    # 1. Check if user exists
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # 2. Find valid OTP for this user
    # We need an OTP that:
    # - Belongs to this user
    # - Has matching purpose
    # - Not yet used
    # - Not expired
    result = await db.execute(
        select(Otp).where(
            and_(
                Otp.user_id == user.id,
                Otp.purpose == purpose,
                Otp.is_used == False,
                Otp.expires_at > datetime.utcnow()
            )
        ).order_by(Otp.created_at.desc())  # Get most recent OTP
    )
    otp_record = result.scalar_one_or_none()

    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid OTP found. Please request a new one."
        )

    # 3. Verify OTP matches
    if otp_record.otp != otp_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )

    # 4. Mark OTP as used (prevent reuse)
    otp_record.is_used = True

    # 5. Mark user as verified
    user.is_verified = True

    await db.commit()
    await db.refresh(user)

    return user


async def expire_old_otps(
    db: AsyncSession,
    user_id: int,
    purpose: str = "REGISTER"
) -> None:
    """
    Mark all unused OTPs for a user as used.

    This is called before generating a new OTP to invalidate previous ones.

    Args:
        db: Database session
        user_id: User ID
        purpose: Purpose of OTPs to expire

    Why expire old OTPs?
    - If user requests new OTP, old ones should be invalid
    - Prevents confusion ("which OTP do I use?")
    - Security: Reduces number of valid OTPs at any time
    """
    result = await db.execute(
        select(Otp).where(
            and_(
                Otp.user_id == user_id,
                Otp.purpose == purpose,
                Otp.is_used == False
            )
        )
    )
    old_otps = result.scalars().all()

    for otp in old_otps:
        otp.is_used = True

    await db.commit()


async def resend_otp(
    db: AsyncSession,
    email: str
) -> tuple[str, str]:
    """
    Resend OTP to user's email.

    Args:
        db: Database session
        email: User's email

    Returns:
        Tuple of (otp_code, username)

    Raises:
        HTTPException: If user not found or already verified

    Process:
    1. Check user exists
    2. Check user not already verified
    3. Expire old OTPs
    4. Generate new OTP
    5. Return OTP to be sent via email
    """
    # Check if user exists
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if user already verified
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )

    # Expire old OTPs
    await expire_old_otps(db, user.id, purpose="REGISTER")

    # Generate new OTP
    otp_code = await create_otp(db, user.id, purpose="REGISTER")

    return otp_code, user.username
