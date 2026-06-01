"""Controlador (MVC) — Streamlit.

Conecta:
  - VISTAS:     ui/views.py
  - PLANTILLAS: ui/templates.py
  - MODELO:     analyzer/ (pipeline, downloader)

Run:  streamlit run app.py
"""
import streamlit as st

from analyzer import pipeline, downloader
from ui import views

st.set_page_config(page_title="Class Analyzer", page_icon="🎓", layout="wide")

# --- Vistas estáticas ---
views.view_header()
cfg, ai_enabled, want_transcript = views.view_sidebar_config()
source = views.view_input()

# --- Acción ---
st.subheader("2. Analizar")
if st.button("▶ Analizar clase", type="primary", use_container_width=True):
    if not source:
        st.error("Indica una ruta local o una URL de video.")
        st.stop()

    status = st.status("Procesando...", expanded=True)

    def log(msg):
        status.write(msg)

    try:
        # 1) Resolver fuente (descarga si es URL)
        video_path = downloader.resolve_source(source, log=log)
        # 2) Pipeline (modelo)
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

    # 3) Render resultados (vista)
    views.view_results(result)
