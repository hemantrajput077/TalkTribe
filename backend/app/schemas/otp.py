from pydantic import BaseModel, EmailStr, Field


class VerifyEmailRequest(BaseModel):
    """
    Request schema for email verification endpoint.

    User provides their email and the OTP they received.
    """
    email: EmailStr
    otp: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="6-digit OTP received via email"
    )


class ResendOTPRequest(BaseModel):
    """
    Request schema for resending OTP.

    User provides only their email to get a new OTP.
    """
    email: EmailStr


class OTPResponse(BaseModel):
    """
    Generic response for OTP-related operations.
    """
    message: str
