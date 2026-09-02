from pydantic import BaseModel

from app.domains.auth.domain.enums import AccountStatus, UserRole


class AuthenticatedIdentity(BaseModel):
    user_id: int
    role: UserRole
    account_status: AccountStatus
    is_verified: bool
