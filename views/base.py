"""Compartido por los routers de vistas: rutas base y motor de plantillas.

`templates/` y `static/` viven en la raiz del proyecto (un nivel arriba de
este paquete).
"""
import os

from fastapi.templating import Jinja2Templates

# Raiz del proyecto = carpeta padre de views/
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)
