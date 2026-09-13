from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from app.domains.profile.infrastructure.user_interest_model import UserInterest


class Interest(Base):
    __tablename__ = "interests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    user_interests: Mapped[list[UserInterest]] = relationship(
        "UserInterest", back_populates="interest", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Interest(id={self.id}, name='{self.name}')>"
