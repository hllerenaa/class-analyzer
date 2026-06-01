"""Acceso a datos (DAO) sobre el ORM de `models.py`.

Define el esquema (clases ORM) en `models.py`; aqui van las consultas. Las
funciones devuelven dict/valores planos para que las vistas y plantillas no
dependan de SQLAlchemy.
"""
import json

from sqlalchemy import select, delete

from models import Setting, ProviderCred, History, get_sessionmaker, create_all

DEFAULT_THRESHOLDS = {
    "min_flag_minutes": 10,
    "motion_playback": 12.0,
    "speech_ratio_low": 0.15,
    "silence_noise_db": -30,
    "silence_min_dur": 0.5,
}


def init():
    """Crea las tablas en PostgreSQL si no existen (idempotente)."""
    create_all()


# --- settings (key/value) -------------------------------------------------

def get_setting(key, default=None):
    with get_sessionmaker()() as s:
        row = s.get(Setting, key)
        return row.value if row else default


def set_setting(key, value):
    with get_sessionmaker()() as s:
        s.merge(Setting(key=key, value=str(value)))
        s.commit()


def get_thresholds():
    raw = get_setting("thresholds")
    if not raw:
        return dict(DEFAULT_THRESHOLDS)
    try:
        return {**DEFAULT_THRESHOLDS, **json.loads(raw)}
    except (ValueError, TypeError):
        return dict(DEFAULT_THRESHOLDS)


def save_thresholds(thr):
    set_setting("thresholds", json.dumps(thr))


# --- credenciales por proveedor IA ---------------------------------------

def get_creds(provider):
    """Devuelve dict {api_key, model, base_url} o None si no hay nada guardado."""
    with get_sessionmaker()() as s:
        row = s.get(ProviderCred, provider)
        if not row:
            return None
        return {"api_key": row.api_key, "model": row.model, "base_url": row.base_url}


def save_creds(provider, api_key="", model="", base_url=""):
    with get_sessionmaker()() as s:
        s.merge(ProviderCred(
            provider=provider, api_key=api_key, model=model, base_url=base_url,
        ))
        s.commit()


def all_creds():
    """{provider: {api_key, model, base_url}} para todos los guardados."""
    with get_sessionmaker()() as s:
        rows = s.scalars(select(ProviderCred)).all()
        return {r.provider: {"api_key": r.api_key, "model": r.model,
                             "base_url": r.base_url} for r in rows}


def load_config(provider):
    """Arma el dict `cfg` que espera analyzer.pipeline desde lo guardado."""
    creds = get_creds(provider) or {"api_key": "", "model": "", "base_url": ""}
    return {
        "ffmpeg_dir": get_setting("ffmpeg_dir", "") or "",
        "provider": provider,
        "model": creds["model"],
        "api_key": creds["api_key"],
        "base_url": creds["base_url"],
        "thresholds": get_thresholds(),
    }


# --- historial de analisis ------------------------------------------------

def _history_to_dict(h):
    return {
        "id": h.id,
        "created_at": h.created_at,
        "source": h.source,
        "duration_min": h.duration_min,
        "speech_ratio": h.speech_ratio,
        "playback_ratio": h.playback_ratio,
        "num_flags": h.num_flags,
        "flagged_minutes": h.flagged_minutes,
        "report": h.report,
        "result_json": h.result_json,
    }


def save_analysis(source, result):
    """Guarda 1 analisis. Devuelve el id insertado."""
    s_sum = result["summary"]
    light = {k: v for k, v in result.items()
             if k not in ("motion", "playback", "speech")}
    with get_sessionmaker()() as s:
        row = History(
            source=source,
            duration_min=s_sum.get("duration_min"),
            speech_ratio=s_sum.get("speech_ratio"),
            playback_ratio=s_sum.get("playback_ratio"),
            num_flags=s_sum.get("num_flags"),
            flagged_minutes=s_sum.get("flagged_minutes"),
            report=result.get("report"),
            result_json=json.dumps(light, ensure_ascii=False),
        )
        s.add(row)
        s.commit()
        return row.id


def list_history(limit=50):
    with get_sessionmaker()() as s:
        rows = s.scalars(
            select(History).order_by(History.id.desc()).limit(limit)
        ).all()
        return [_history_to_dict(r) for r in rows]


def get_history(hid):
    with get_sessionmaker()() as s:
        row = s.get(History, hid)
        return _history_to_dict(row) if row else None


def delete_history(hid):
    with get_sessionmaker()() as s:
        s.execute(delete(History).where(History.id == hid))
        s.commit()


def clear_history():
    with get_sessionmaker()() as s:
        s.execute(delete(History))
        s.commit()
