from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class Otp(Base):
    __tablename__ = "otps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    otp: Mapped[str] = mapped_column(String(6), nullable=False)

    purpose: Mapped[str] = mapped_column(String(30), nullable=False)

    expires_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)

    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self):
        return (
            f"<Otp(id={self.id}, user_id={self.user_id}, "
            f"purpose='{self.purpose}', is_used={self.is_used})>"
        )

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        if isinstance(other, Otp):
            return self.id == other.id
        return False
