"""VISTAS (MVC): funciones que renderizan cada sección de la UI.

Cada función `view_*` dibuja una parte y, si aplica, devuelve datos del usuario.
No contienen lógica de negocio (esa vive en analyzer/).
"""
import os
import json
import tempfile
import streamlit as st

from . import templates as T


def view_header():
    """Vista: título, descripción y panel de ayuda."""
    st.title(T.APP_TITLE)
    st.caption(T.APP_CAPTION)
    with st.expander("📖 Cómo instalar y cómo funciona"):
        st.markdown(T.HELP_MD)


def view_provider_help(provider):
    """Vista: ayuda de token/conexión del proveedor seleccionado."""
    info = T.PROVIDER_INFO[provider]
    badge = "🟢 GRATIS" if info["gratis"] else "💲 De pago"
    st.caption(f"**{info['nombre']}** — {badge}")
    with st.expander("ℹ️ Cómo obtener token / conectar",
                     expanded=(provider != "ollama")):
        if provider == "ollama":
            st.markdown("**No necesita token.** Es local. Pasos:")
        else:
            st.markdown(f"[🔑 Generar API token aquí]({info['token_url']})")
        for i, p in enumerate(info["pasos"], 1):
            st.markdown(f"{i}. {p}")
        st.markdown(
            f"[📄 Docs API]({info['docs_url']}) · "
            f"[📦 Modelos disponibles]({info['modelos_url']})"
        )


def view_sidebar_config():
    """Vista: sidebar de configuración. Devuelve dict cfg + flags de ejecución."""
    with st.sidebar:
        st.header("⚙️ Configuración")
        provider = st.selectbox(
            "Proveedor de IA",
            ["ollama", "claude", "gemini", "deepseek"],
            help="ollama = local/gratis. Otros requieren token.",
        )
        view_provider_help(provider)

        api_key = st.text_input(
            "API Token", type="password",
            help="No requerido para ollama local.",
            disabled=(provider == "ollama"),
        )
        model = st.text_input("Modelo", value=T.MODEL_HINTS[provider])
        base_url = st.text_input(
            "Base URL (opcional)",
            help="Override del endpoint. Ej. ollama remoto.",
        )
        ffmpeg_dir = st.text_input(
            "Carpeta ffmpeg (opcional)",
            help="Vacío = autodetectar (PATH o winget).",
        )

        st.divider()
        st.subheader("Umbrales de detección")
        min_flag = st.number_input("Min minutos para flag", 1, 120, 10)
        motion_thr = st.slider("Umbral movimiento (playback)", 1.0, 40.0, 12.0)
        speech_low = st.slider("Voz docente baja (<)", 0.0, 1.0, 0.15)
        noise_db = st.slider("Umbral silencio (dB)", -60, -10, -30)

        st.divider()
        ai_enabled = st.checkbox("Generar reporte con IA", value=True)
        want_transcript = st.checkbox(
            "Transcribir (faster-whisper)", value=False,
            help="Requiere 'pip install faster-whisper'. Más lento.",
        )

    cfg = {
        "ffmpeg_dir": ffmpeg_dir,
        "provider": provider,
        "model": model,
        "api_key": api_key,
        "base_url": base_url,
        "thresholds": {
            "min_flag_minutes": min_flag,
            "motion_playback": motion_thr,
            "speech_ratio_low": speech_low,
            "silence_noise_db": noise_db,
            "silence_min_dur": 0.5,
        },
    }
    return cfg, ai_enabled, want_transcript


def view_input():
    """Vista: entrada de video (ruta local, URL, o subida).
    Devuelve la 'fuente' (str): ruta local o URL.
    """
    st.subheader("1. Video de la clase")
    source = st.text_input(
        "Ruta local o URL",
        placeholder="C:\\...\\clase.mp4  |  https://youtube.com/watch?v=...",
        help="Acepta archivo local o URL (YouTube/Drive). "
             "SharePoint/Teams: descarga manual.",
    )
    upload = st.file_uploader(
        "...o sube un archivo", type=["mp4", "mov", "mkv", "avi"]
    )
    if upload is not None:
        suffix = os.path.splitext(upload.name)[1]
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(upload.read())
        tmp.close()
        source = tmp.name
        st.info(f"Archivo subido → {source}")
    return source


def view_results(result):
    """Vista: métricas, flags, reporte IA y descargas."""
    s = result["summary"]
    st.subheader("3. Resultados")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Duración", f"{s['duration_min']} min")
    c2.metric("Voz activa", f"{round(s['speech_ratio']*100)}%")
    c3.metric("Playback video", f"{round(s['playback_ratio']*100)}%")
    c4.metric("Flags", s["num_flags"])

    if result["flags"]:
        st.error(f"⚠ {s['num_flags']} segmento(s) sospechoso(s) — "
                 f"{s['flagged_minutes']} min")
        st.table([
            {"Tipo": f["type"],
             "Inicio": f"{f['start']//60:02d}:{f['start']%60:02d}",
             "Fin": f"{f['end']//60:02d}:{f['end']%60:02d}",
             "Min": f["duration_sec"] // 60,
             "Voz %": round(f["speech_ratio"] * 100)}
            for f in result["flags"]
        ])
    else:
        st.success("Sin segmentos de 'video sin clase' detectados.")

    if result.get("report"):
        st.subheader("📋 Reporte IA")
        st.markdown(result["report"])
        st.download_button("Descargar reporte (.md)", result["report"],
                           file_name="reporte_clase.md")

    if result.get("transcript"):
        with st.expander("Ver transcripción"):
            st.text(result["transcript"])

    st.download_button(
        "Descargar JSON crudo",
        json.dumps({k: v for k, v in result.items()
                    if k not in ("motion", "playback", "speech")},
                   ensure_ascii=False, indent=2),
        file_name="analisis.json",
    )
