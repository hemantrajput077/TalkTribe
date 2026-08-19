from pydantic import BaseModel, EmailStr, Field


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    otp: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="6-digit OTP received via email",
    )


class ResendOTPRequest(BaseModel):
    email: EmailStr


class OTPResponse(BaseModel):
    message: str
