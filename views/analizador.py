"""ROUTER: Analizador. Form de analisis y ejecucion del pipeline.

Rutas:
  GET  /          pagina principal (form + historial)
  POST /analizar  corre el pipeline y renderiza resultados
"""
import os
import tempfile

from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse

from analyzer import pipeline, downloader, store
from . import content
from .base import templates

router = APIRouter()


def _active_cfg():
    """cfg de IA del proveedor activo guardado (para prefill del formulario)."""
    provider = store.get_setting("provider", "ollama")
    creds = store.get_creds(provider) or {}
    return {
        "provider": provider,
        "api_key": creds.get("api_key", ""),
        "model": creds.get("model") or content.MODEL_HINTS[provider],
        "base_url": creds.get("base_url", ""),
        "ffmpeg_dir": store.get_setting("ffmpeg_dir", "") or "",
    }


@router.get("/", response_class=HTMLResponse)
def home(request: Request, saved: int = 0):
    return templates.TemplateResponse(request, "index.html", {
        "active": "home", "content": content,
        "cfg": _active_cfg(), "thr": store.get_thresholds(),
        "history": store.list_history(limit=50), "saved": bool(saved),
    })


@router.post("/analizar", response_class=HTMLResponse)
async def analizar(
    request: Request,
    source: str = Form(""),
    upload: UploadFile | None = File(None),
    provider: str = Form("ollama"),
    api_key: str = Form(""),
    model: str = Form(""),
    base_url: str = Form(""),
    ffmpeg_dir: str = Form(""),
    min_flag_minutes: int = Form(10),
    motion_playback: float = Form(12.0),
    speech_ratio_low: float = Form(0.15),
    silence_noise_db: int = Form(-30),
    ai_enabled: str | None = Form(None),
    want_transcript: str | None = Form(None),
    save_config: str | None = Form(None),
):
    thr_prev = store.get_thresholds()
    cfg = {
        "ffmpeg_dir": ffmpeg_dir,
        "provider": provider,
        "model": model,
        "api_key": api_key,
        "base_url": base_url,
        "thresholds": {
            "min_flag_minutes": min_flag_minutes,
            "motion_playback": motion_playback,
            "speech_ratio_low": speech_ratio_low,
            "silence_noise_db": silence_noise_db,
            "silence_min_dur": thr_prev.get("silence_min_dur", 0.5),
        },
    }

    if save_config is not None:
        store.set_setting("provider", provider)
        store.set_setting("ffmpeg_dir", ffmpeg_dir)
        store.save_thresholds(cfg["thresholds"])
        store.save_creds(provider, api_key=api_key, model=model, base_url=base_url)

    # Fuente: archivo subido tiene prioridad sobre el texto.
    if upload is not None and upload.filename:
        suffix = os.path.splitext(upload.filename)[1]
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(await upload.read())
        tmp.close()
        source = tmp.name

    if not source:
        return templates.TemplateResponse(request, "error.html", {
            "active": "home",
            "message": "Indica una ruta local o una URL de video (o sube un archivo).",
        }, status_code=400)

    try:
        video_path = downloader.resolve_source(source, log=lambda m: None)
        result = pipeline.analyze(
            video_path, cfg,
            want_transcript=(want_transcript is not None),
            ai_enabled=(ai_enabled is not None),
            log=lambda m: None,
        )
    except Exception as e:  # noqa: BLE001 — superficie de error a la vista
        return templates.TemplateResponse(request, "error.html", {
            "active": "home",
            "message": f"{type(e).__name__}: {e}",
        }, status_code=500)

    history_id = None
    try:
        history_id = store.save_analysis(source, result)
    except Exception:
        pass

    return templates.TemplateResponse(request, "resultados.html", {
        "active": "home",
        "source": source, "result": result, "history_id": history_id,
    })
