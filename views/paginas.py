"""ROUTER: paginas informativas y configuracion.

Rutas:
  GET  /como-usar             guia de uso
  GET  /docs-tokens           docs por proveedor + form de credenciales
  POST /guardar-credenciales  guarda token/modelo/base_url en la BD
"""
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from analyzer import store
from . import content
from .base import templates

router = APIRouter()


@router.get("/como-usar", response_class=HTMLResponse)
def como_usar(request: Request):
    return templates.TemplateResponse(request, "como_usar.html", {
        "active": "howto", "content": content,
    })


@router.get("/docs-tokens", response_class=HTMLResponse)
def docs_tokens(request: Request, saved: str = ""):
    sel = store.get_setting("provider", "ollama")
    creds = store.get_creds(sel) or {"api_key": "", "model": content.MODEL_HINTS[sel], "base_url": ""}
    return templates.TemplateResponse(request, "docs_tokens.html", {
        "active": "docs", "content": content,
        "sel_provider": sel, "creds": creds,
        "saved_all": store.all_creds(), "saved": saved,
    })


@router.post("/guardar-credenciales")
def guardar_credenciales(
    provider: str = Form(...),
    api_key: str = Form(""),
    model: str = Form(""),
    base_url: str = Form(""),
    set_active: str | None = Form(None),
):
    store.save_creds(provider, api_key=api_key, model=model, base_url=base_url)
    if set_active is not None:
        store.set_setting("provider", provider)
    return RedirectResponse(url=f"/docs-tokens?saved={provider}", status_code=303)
