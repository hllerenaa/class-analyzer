"""Modelo History: un analisis ejecutado."""
from datetime import datetime

from sqlalchemy import Integer, Float, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class History(Base):
    __tablename__ = "history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    source: Mapped[str | None] = mapped_column(Text)
    duration_min: Mapped[float | None] = mapped_column(Float)
    speech_ratio: Mapped[float | None] = mapped_column(Float)
    playback_ratio: Mapped[float | None] = mapped_column(Float)
    num_flags: Mapped[int | None] = mapped_column(Integer)
    flagged_minutes: Mapped[float | None] = mapped_column(Float)
    report: Mapped[str | None] = mapped_column(Text)
    result_json: Mapped[str | None] = mapped_column(Text)
