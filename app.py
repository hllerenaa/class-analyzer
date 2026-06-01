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
    "ollama": "llama3.2:3b",
}

# Info por proveedor: donde sacar token + docs + como conectar.
PROVIDER_INFO = {
    "claude": {
        "nombre": "Anthropic Claude",
        "token_url": "https://console.anthropic.com/settings/keys",
        "docs_url": "https://docs.anthropic.com/en/api/getting-started",
        "modelos_url": "https://docs.anthropic.com/en/docs/about-claude/models",
        "pasos": [
            "Crea cuenta en console.anthropic.com",
            "Settings → API Keys → Create Key",
            "Copia la key (sk-ant-...) y pegala en 'API Token'",
            "Carga saldo en Billing (de pago, ~\\$0.02/clase con Haiku)",
        ],
        "gratis": False,
    },
    "gemini": {
        "nombre": "Google Gemini",
        "token_url": "https://aistudio.google.com/app/apikey",
        "docs_url": "https://ai.google.dev/gemini-api/docs",
        "modelos_url": "https://ai.google.dev/gemini-api/docs/models",
        "pasos": [
            "Entra a aistudio.google.com con tu cuenta Google",
            "Get API key → Create API key",
            "Copia la key y pegala en 'API Token'",
            "Tiene capa gratuita con limites de uso",
        ],
        "gratis": True,
    },
    "deepseek": {
        "nombre": "DeepSeek",
        "token_url": "https://platform.deepseek.com/api_keys",
        "docs_url": "https://api-docs.deepseek.com/",
        "modelos_url": "https://api-docs.deepseek.com/quick_start/pricing",
        "pasos": [
            "Crea cuenta en platform.deepseek.com",
            "API keys → Create new API key",
            "Copia la key y pegala en 'API Token'",
            "Recarga saldo (muy barato)",
        ],
        "gratis": False,
    },
    "ollama": {
        "nombre": "Ollama (LOCAL, $0)",
        "token_url": "https://ollama.com/download",
        "docs_url": "https://github.com/ollama/ollama/blob/main/README.md",
        "modelos_url": "https://ollama.com/library",
        "pasos": [
            "Instala: winget install Ollama.Ollama (o descarga de ollama.com)",
            "El server arranca solo en http://localhost:11434",
            "Descarga un modelo: ollama pull llama3.2:3b",
            "NO necesita token. Deja 'API Token' vacio.",
            "Base URL solo si Ollama esta en otra maquina.",
        ],
        "gratis": True,
    },
}

st.title("🎓 Class Analyzer — debilidades en grabaciones de clase")
st.caption(
    "Deteccion local (ffmpeg, sin costo) + IA pluggable para el reporte. "
    "Detecta p.ej. >10 min de video compartido sin clase activa."
)

with st.expander("📖 Cómo instalar y cómo funciona"):
    st.markdown(
        """
### ¿Qué hace?
Analiza una grabación de clase y detecta debilidades. Caso clave:
**>10 min de video compartido donde el docente no dio clase activa.**

### ¿Cómo funciona? (2 capas)
1. **Detección local (sin IA, $0)** — `ffmpeg` + `numpy`:
   - **VAD por silencio**: cuánto habla el docente.
   - **Movimiento entre frames**: detecta video reproduciéndose en pantalla.
   - **Motor de reglas**: marca segmentos sospechosos.
2. **IA (opcional, pluggable)** — solo redacta el reporte sobre las señales
   ya detectadas. El video **nunca** se manda a la IA (sería caro): solo texto.

### Instalar la aplicación
```bash
# 1) ffmpeg (obligatorio)
winget install Gyan.FFmpeg          # Windows
sudo apt install ffmpeg             # Linux

# 2) Dependencias Python
pip install -r requirements.txt

# 3) (opcional) transcript local
pip install faster-whisper

# 4) Correr
streamlit run app.py
```
Repo: https://github.com/hllerenaa/class-analyzer ·
Guía de producción: ver `DEPLOYMENT.md` · Guía de IA: ver `GUIA_IA.md`

### Instalar IA local (Ollama, $0)
```bash
winget install Ollama.Ollama        # Windows  (o https://ollama.com/download)
curl -fsSL https://ollama.com/install.sh | sh   # Linux
ollama pull llama3.2:3b             # descarga el modelo (~2 GB)
```
El server queda en `http://localhost:11434`. En el sidebar elige provider
`ollama`, sin token. Listo.

### Usar IA en la nube (token)
En el sidebar elige el provider y abre **"Cómo obtener token"** — ahí está
el link directo para generar tu API key de cada proveedor.
"""
    )

# ---------------- Sidebar config ----------------
with st.sidebar:
    st.header("⚙️ Configuracion")

    provider = st.selectbox(
        "Proveedor de IA",
        ["ollama", "claude", "gemini", "deepseek"],
        help="ollama = local/gratis. Otros requieren token.",
    )

    info = PROVIDER_INFO[provider]
    badge = "🟢 GRATIS" if info["gratis"] else "💲 De pago"
    st.caption(f"**{info['nombre']}** — {badge}")
    with st.expander("ℹ️ Cómo obtener token / conectar", expanded=(provider != "ollama")):
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

    api_key = st.text_input(
        "API Token", type="password",
        help="No requerido para ollama local.",
        disabled=(provider == "ollama"),
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
