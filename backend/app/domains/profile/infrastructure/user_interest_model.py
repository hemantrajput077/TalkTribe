from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from app.domains.profile.infrastructure.interest_model import Interest


class UserInterest(Base):
    """
    Join table: which interests a user has selected.

    Composite PK (user_id, interest_id).
    Rows are deleted automatically when either the user or the interest is deleted.
    """

    __tablename__ = "user_interests"

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        index=True,
    )
    interest_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("interests.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    interest: Mapped[Interest] = relationship("Interest", back_populates="user_interests")

    def __repr__(self) -> str:
        return f"<UserInterest(user_id={self.user_id}, interest_id={self.interest_id})>"
