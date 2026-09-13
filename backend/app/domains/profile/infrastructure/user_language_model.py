from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base


class UserLanguage(Base):
    __tablename__ = "user_languages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    language_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("languages.id"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    proficiency: Mapped[str | None] = mapped_column(String(5), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "language_id", "role", name="uq_user_language_role"),
    )

    language = relationship("Language", back_populates="user_languages")

    @property
    def language_name(self) -> str:
        return self.language.name

    @property
    def language_code(self) -> str:
        return self.language.code

    def __repr__(self) -> str:
        return f"<UserLanguage(user_id={self.user_id}, language_id={self.language_id}, role='{self.role}')>"
