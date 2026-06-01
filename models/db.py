"""Conexion y base del ORM: credenciales, engine PostgreSQL, sesiones, Base.

La conexion se lee de `credentials.json` (raiz) con override por entorno:
    ip/DB_IP · port/DB_PORT · username/DB_USERNAME · password/DB_PASSWORD · dbname/DB_NAME

Driver: psycopg v3  ->  URL "postgresql+psycopg://..."
"""
import os
import json

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Ruta de credenciales (override con DB_CREDENTIALS_PATH).
CRED_PATH = os.environ.get(
    "DB_CREDENTIALS_PATH",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "credentials.json"),
)


def load_credentials():
    """Lee credentials.json y aplica overrides por entorno."""
    data = {}
    if os.path.exists(CRED_PATH):
        with open(CRED_PATH, encoding="utf-8") as f:
            data = json.load(f)
    return {
        "host": os.environ.get("DB_IP", data.get("ip", "127.0.0.1")),
        "port": int(os.environ.get("DB_PORT", data.get("port", 5432))),
        "user": os.environ.get("DB_USERNAME", data.get("username", "class_analyzer")),
        "password": os.environ.get("DB_PASSWORD", data.get("password", "")),
        "dbname": os.environ.get("DB_NAME", data.get("dbname", "class_analyzer")),
    }


def _url():
    c = load_credentials()
    return URL.create(
        "postgresql+psycopg",
        username=c["user"], password=c["password"],
        host=c["host"], port=c["port"], database=c["dbname"],
    )


class Base(DeclarativeBase):
    pass


_engine = None
_Session = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(_url(), pool_pre_ping=True, future=True)
    return _engine


def get_sessionmaker():
    global _Session
    if _Session is None:
        _Session = sessionmaker(bind=get_engine(), expire_on_commit=False, future=True)
    return _Session


def create_all():
    """Crea las tablas en PostgreSQL si no existen (idempotente)."""
    Base.metadata.create_all(get_engine())
