"""UI Streamlit: analiza grabaciones de clase y detecta debilidades.

Run:  streamlit run app.py
"""
import os
import json
import tempfile
import streamlit as st

from analyzer import pipeline

st.set_page_config(page_title="Class Analyzer", page_icon="🎓", layout="wide")

DEFAULTS = {
    "ffmpeg_dir": "",
    "provider": "ollama",
    "model": "llama3.1",
    "api_key": "",
    "base_url": "",
    "thresholds": {
        "min_flag_minutes": 10,
        "motion_playback": 12.0,
        "speech_ratio_low": 0.15,
        "silence_noise_db": -30,
        "silence_min_dur": 0.5,
    },
}

MODEL_HINTS = {
    "claude": "claude-3-5-haiku-latest",
    "gemini": "gemini-1.5-flash",
    "deepseek": "deepseek-chat",
    "ollama": "llama3.1",
}

st.title("🎓 Class Analyzer — debilidades en grabaciones de clase")
st.caption(
    "Deteccion local (ffmpeg, sin costo) + IA pluggable para el reporte. "
    "Detecta p.ej. >10 min de video compartido sin clase activa."
)

# ---------------- Sidebar config ----------------
with st.sidebar:
    st.header("⚙️ Configuracion")

    provider = st.selectbox(
        "Proveedor de IA",
        ["ollama", "claude", "gemini", "deepseek"],
        help="ollama = local/gratis. Otros requieren token.",
    )
    api_key = st.text_input(
        "API Token", type="password",
        help="No requerido para ollama local.",
    )
    model = st.text_input("Modelo", value=MODEL_HINTS[provider])
    base_url = st.text_input(
        "Base URL (opcional)",
        help="Override del endpoint. Ej. ollama remoto.",
    )
    ffmpeg_dir = st.text_input(
        "Carpeta ffmpeg (opcional)",
        help="Dejar vacio para autodetectar (PATH o winget).",
    )

    st.divider()
    st.subheader("Umbrales de deteccion")
    min_flag = st.number_input("Min minutos para flag", 1, 120, 10)
    motion_thr = st.slider("Umbral movimiento (playback)", 1.0, 40.0, 12.0)
    speech_low = st.slider("Voz docente baja (<)", 0.0, 1.0, 0.15)
    noise_db = st.slider("Umbral silencio (dB)", -60, -10, -30)

    st.divider()
    ai_enabled = st.checkbox("Generar reporte con IA", value=True)
    want_transcript = st.checkbox(
        "Transcribir (faster-whisper)", value=False,
        help="Requiere 'pip install faster-whisper'. Mas lento.",
    )

# ---------------- Input video ----------------
st.subheader("1. Video de la clase")
col1, col2 = st.columns(2)
with col1:
    video_path = st.text_input(
        "Ruta local del video",
        placeholder=r"C:\Users\aaron\Downloads\clase.mp4",
    )
with col2:
    upload = st.file_uploader("...o sube un archivo", type=["mp4", "mov", "mkv", "avi"])

if upload is not None:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(upload.name)[1])
    tmp.write(upload.read())
    tmp.close()
    video_path = tmp.name
    st.info(f"Archivo subido → {video_path}")

# ---------------- Run ----------------
st.subheader("2. Analizar")
if st.button("▶ Analizar clase", type="primary", use_container_width=True):
    if not video_path or not os.path.isfile(video_path):
        st.error("Ruta de video invalida.")
        st.stop()

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

    status = st.status("Procesando...", expanded=True)

    def log(msg):
        status.write(msg)

    try:
        result = pipeline.analyze(
            video_path, cfg,
            want_transcript=want_transcript,
            ai_enabled=ai_enabled,
            log=log,
        )
        status.update(label="Listo", state="complete")
    except Exception as e:
        status.update(label="Error", state="error")
        st.exception(e)
        st.stop()

    # ---- Resultados ----
    s = result["summary"]
    m = result["meta"]
    st.subheader("3. Resultados")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Duracion", f"{s['duration_min']} min")
    c2.metric("Voz activa", f"{round(s['speech_ratio']*100)}%")
    c3.metric("Playback video", f"{round(s['playback_ratio']*100)}%")
    c4.metric("Flags", s["num_flags"])

    if result["flags"]:
        st.error(f"⚠ {s['num_flags']} segmento(s) sospechoso(s) — "
                 f"{s['flagged_minutes']} min")
        st.table([
            {"Tipo": f["type"], "Inicio": f"{f['start']//60:02d}:{f['start']%60:02d}",
             "Fin": f"{f['end']//60:02d}:{f['end']%60:02d}",
             "Min": f["duration_sec"]//60,
             "Voz %": round(f["speech_ratio"]*100)}
            for f in result["flags"]
        ])
    else:
        st.success("Sin segmentos de 'video sin clase' detectados.")

    if result["report"]:
        st.subheader("📋 Reporte IA")
        st.markdown(result["report"])
        st.download_button(
            "Descargar reporte (.md)",
            result["report"],
            file_name="reporte_clase.md",
        )

    if result["transcript"]:
        with st.expander("Ver transcripcion"):
            st.text(result["transcript"])

    st.download_button(
        "Descargar JSON crudo",
        json.dumps({k: v for k, v in result.items()
                    if k not in ("motion", "playback", "speech")},
                   ensure_ascii=False, indent=2),
        file_name="analisis.json",
    )
