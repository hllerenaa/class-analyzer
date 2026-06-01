"""Paquete MODELOS (SQLAlchemy ORM) + engine PostgreSQL.

Aqui vive la definicion del *modelo* de la base de datos. `create_all()` crea
las tablas a partir de estas clases.

  - db.py             engine, sesiones, Base, credenciales, create_all
  - setting.py        modelo Setting
  - provider_cred.py  modelo ProviderCred
  - history.py        modelo History

Importar los modelos aqui los registra en `Base.metadata` (necesario para
que `create_all()` los vea).
"""
from .db import (
    Base, load_credentials, get_engine, get_sessionmaker, create_all,
)
from .setting import Setting
from .provider_cred import ProviderCred
from .history import History

__all__ = [
    "Base", "load_credentials", "get_engine", "get_sessionmaker", "create_all",
    "Setting", "ProviderCred", "History",
]
