"""ROUTER: historial de analisis (almacenado en la BD).

Rutas:
  POST /historial/vaciar          borra todo el historial
  GET  /historial/{hid}           detalle de un analisis
  GET  /historial/{hid}/reporte   descarga el reporte (.md)
  GET  /historial/{hid}/json      descarga el JSON crudo
"""
import json

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from analyzer import store
from .base import templates

router = APIRouter(prefix="/historial")


@router.post("/vaciar")
def vaciar():
    store.clear_history()
    return RedirectResponse(url="/", status_code=303)


@router.get("/{hid}", response_class=HTMLResponse)
def detalle(request: Request, hid: int):
    rec = store.get_history(hid)
    if not rec:
        return templates.TemplateResponse(request, "error.html", {
            "active": "home", "message": "Analisis no encontrado.",
        }, status_code=404)
    return templates.TemplateResponse(request, "historial_detalle.html", {
        "active": "home", "rec": rec,
    })


@router.get("/{hid}/reporte")
def reporte(hid: int):
    rec = store.get_history(hid)
    if not rec or not rec.get("report"):
        return Response("Sin reporte.", status_code=404, media_type="text/plain")
    return Response(
        rec["report"], media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="reporte_{hid}.md"'},
    )


@router.get("/{hid}/json")
def historial_json(hid: int):
    rec = store.get_history(hid)
    if not rec:
        return Response("No encontrado.", status_code=404, media_type="text/plain")
    return Response(
        rec["result_json"] or json.dumps({}), media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="analisis_{hid}.json"'},
    )
