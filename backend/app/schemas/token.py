from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class RefreshRequest(BaseModel):
    """Body for the /auth/refresh endpoint."""
    refresh_token: str


class LogoutRequest(BaseModel):
    """Body for the /auth/logout endpoint."""
    refresh_token: str


class TokenPayload(BaseModel):
    """Validated contents of a decoded JWT payload."""
    sub: str        # user_id as string
    email: str
    type: str       # "access" | "refresh"
    jti: str        # unique token ID