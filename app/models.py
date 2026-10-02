from sqlalchemy import String, JSON, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base

import uuid



class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)




class GameSession(Base):
    __tablename__ = "game_sessions"

    __table_args__ = (
        CheckConstraint(
            "status IN ('opened', 'closed')",
            name="ck_game_sessions_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
        default=uuid.uuid4,
    )

    fleet: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="opened",
    )




class Shot(Base):
    __tablename__ = "shots"

    __table_args__ = (
        CheckConstraint(
            "side IN ('self', 'opponent')",
            name="ck_shots_side",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    game_session_id: Mapped[int] = mapped_column(
        ForeignKey("game_sessions.id"),
        nullable=False,
    )

    side: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    row: Mapped[int] = mapped_column(
        nullable=False,
    )

    column: Mapped[int] = mapped_column(
        nullable=False,
    )

    result: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

