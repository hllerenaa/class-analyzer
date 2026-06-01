"""App FastAPI — Class Analyzer. Ensambla los routers de vistas.

Estructura del paquete:
  - base.py        plantillas Jinja2 + rutas base (compartido)
  - analizador.py  ROUTER:  /  y  /analizar
  - paginas.py     ROUTER:  /como-usar, /docs-tokens, /guardar-credenciales
  - historial.py   ROUTER:  /historial/...
  - __init__.py     (este)  crea `app`, monta /static e incluye los routers

Capas:
  - VISTAS/URLs:  views/ (este paquete)
  - PLANTILLAS:   templates/*.html (Jinja2)
  - ESTILO:       static/css/styles.css
  - CONTENIDO:    content.py (datos puros)
  - MODELO:       models.py (ORM) + analyzer/store.py (DAO) -> PostgreSQL
  - LOGICA:       analyzer/ (pipeline, downloader)

Run:  uvicorn views:app --reload
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from analyzer import store
from .base import STATIC_DIR
from . import analizador, paginas, historial

app = FastAPI(title="Class Analyzer")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(analizador.router)
app.include_router(paginas.router)
app.include_router(historial.router)

try:
    store.init()  # crea tablas en PostgreSQL si no existen (idempotente)
except Exception as e:  # la BD puede no estar arriba todavia
    msg = str(e).encode("ascii", "replace").decode("ascii")
    print(f"[store] No se pudo inicializar PostgreSQL: {type(e).__name__}: {msg}")
    print("[store] Levanta la BD: docker compose -f docker-compose.postgres.yml up -d")
