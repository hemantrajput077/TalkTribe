import random
import string


def generate_otp(length: int = 6) -> str:
    """
    Generate a random numeric OTP.

    Args:
        length: Number of digits in OTP (default: 6)

    Returns:
        String of random digits

    Example:
        >>> generate_otp(6)
        "123456"
    """
    return ''.join(random.choices(string.digits, k=length))
