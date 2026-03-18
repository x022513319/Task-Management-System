from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from bcrypt import checkpw, gensalt, hashpw
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.task import Task


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(64), unique=True)
    password_hash: Mapped[str] = mapped_column(String(128))

    tasks: Mapped[list[Task]] = relationship(back_populates="user")

    def set_password(self, password) -> None:
        self.password_hash = hashpw(password.encode("utf-8"), gensalt()).decode("utf-8")

    def verify_password(self, password) -> bool:
        return checkpw(password.encode("utf-8"), self.password_hash.encode("utf-8"))
