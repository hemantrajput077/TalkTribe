from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class RefreshRequest(BaseModel):
    refresh_token: str
    access_token: str


class LogoutRequest(BaseModel):
    refresh_token: str
    access_token: str


class TokenPayload(BaseModel):
    sub: str       # user_id as string
    email: str
    type: str      # "access" | "refresh"
    jti: str       # unique token ID
