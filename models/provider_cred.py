"""Modelo ProviderCred: credenciales de IA por proveedor."""
from datetime import datetime

from sqlalchemy import Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class ProviderCred(Base):
    __tablename__ = "provider_creds"
    provider: Mapped[str] = mapped_column(Text, primary_key=True)
    api_key: Mapped[str] = mapped_column(Text, default="")
    model: Mapped[str] = mapped_column(Text, default="")
    base_url: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
