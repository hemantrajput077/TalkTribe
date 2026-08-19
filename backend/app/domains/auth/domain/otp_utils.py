import secrets


def generate_otp(length: int = 6) -> str:
    """
    Generate a cryptographically secure numeric OTP.
    Uses secrets.randbelow() (OS-level CSPRNG) — not random.choices().
    """
    return "".join(str(secrets.randbelow(10)) for _ in range(length))
