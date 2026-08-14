import secrets


def generate_otp(length: int = 6) -> str:
    """
    Generate a cryptographically secure random numeric OTP.

    Uses secrets.randbelow() (OS-level CSPRNG) instead of random.choices()
    which is predictable and unsuitable for security-sensitive codes.
    """
    return ''.join(str(secrets.randbelow(10)) for _ in range(length))
