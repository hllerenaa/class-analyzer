"""PLANTILLAS de UI (texto, markdown, constantes). Sin lógica de render."""

APP_TITLE = "🎓 Class Analyzer — debilidades en grabaciones de clase"

APP_CAPTION = (
    "Deteccion local (ffmpeg, sin costo) + IA pluggable para el reporte. "
    "Detecta p.ej. >10 min de video compartido sin clase activa."
)

# Orden de proveedores en selects/paginas
PROVIDERS = ["ollama", "claude", "gemini", "deepseek"]

# Modelo sugerido por proveedor
MODEL_HINTS = {
    "claude": "claude-3-5-haiku-latest",
    "gemini": "gemini-1.5-flash",
    "deepseek": "deepseek-chat",
    "ollama": "llama3.2:3b",
}

# Info por proveedor: token, docs, pasos de conexión
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
            "Carga saldo en Billing (~\\$0.02/clase con Haiku)",
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
            "Instala: winget install Ollama.Ollama (o ollama.com)",
            "El server arranca solo en http://localhost:11434",
            "Descarga un modelo: ollama pull llama3.2:3b",
            "NO necesita token. Deja 'API Token' vacio.",
            "Base URL solo si Ollama esta en otra maquina.",
        ],
        "gratis": True,
    },
}

# Markdown del panel de ayuda (instalar + cómo funciona)
HELP_MD = """
### ¿Qué hace?
Analiza una grabación de clase y detecta debilidades. Caso clave:
**>10 min de video compartido donde el docente no dio clase activa.**

### ¿Cómo funciona? (2 capas)
1. **Detección local (sin IA, $0)** — `ffmpeg` + `numpy`:
   - **VAD por silencio**: cuánto habla el docente.
   - **Movimiento entre frames**: detecta video reproduciéndose en pantalla.
   - **Motor de reglas**: marca segmentos sospechosos.
2. **IA (opcional, pluggable)** — solo redacta el reporte sobre las señales
   ya detectadas. El video **nunca** se manda a la IA: solo texto.

### Fuentes de video aceptadas
- Archivo local (ruta o subida).
- **URL**: YouTube, Google Drive y ~1000 sitios (yt-dlp).
- SharePoint/Teams/OneDrive: requieren login → descarga manual y usa la ruta.

### Instalar la aplicación
```bash
winget install Gyan.FFmpeg            # Windows (Linux: sudo apt install ffmpeg)
pip install -r requirements.txt
streamlit run app.py
```
Repo: https://github.com/hllerenaa/class-analyzer ·
Guía ejecución: `EJECUTAR.md` · Producción: `DEPLOYMENT.md` · IA: `GUIA_IA.md`

### IA local (Ollama, $0)
```bash
winget install Ollama.Ollama
ollama pull llama3.2:3b
```
Server en `http://localhost:11434`. En el sidebar elige `ollama`, sin token.
"""

# --- Contenido estructurado para la pagina "Como usar" -------------------

HOWTO_INSTALL = [
    "Instala ffmpeg:  winget install Gyan.FFmpeg  (Linux: sudo apt install ffmpeg)",
    "Instala dependencias:  pip install -r requirements.txt",
    "Arranca la app:  streamlit run app.py",
    "(Opcional) IA local gratis:  winget install Ollama.Ollama  &&  ollama pull llama3.2:3b",
]

HOWTO_USE = [
    "Ve a 'Docs y Tokens' y guarda el proveedor de IA y su token (Ollama no necesita token).",
    "Vuelve a 'Analizador' y pega una ruta local o una URL de video (o sube un archivo).",
    "Ajusta los umbrales en el panel lateral si lo necesitas (o deja los valores por defecto).",
    "Pulsa 'Analizar clase' y espera el procesamiento (probe -> audio -> movimiento -> reglas -> IA).",
    "Revisa metricas, segmentos marcados y el reporte IA. Cada analisis queda en el historial.",
]

# Que hace cada capa (tarjetas en "Como usar")
HOWTO_CARDS = [
    ("🎯", "Que detecta",
     "Debilidades en una grabacion de clase. Caso clave: >10 min de video "
     "compartido en pantalla sin clase activa del docente."),
    ("🔍", "Deteccion local ($0)",
     "ffmpeg + numpy: VAD por silencio (cuanto habla el docente), movimiento "
     "entre frames (playback de video) y un motor de reglas que marca segmentos."),
    ("🤖", "IA solo para el reporte",
     "El proveedor de IA solo redacta el reporte sobre las senales ya detectadas. "
     "El video NUNCA se envia a la IA: solo texto."),
    ("📥", "Fuentes aceptadas",
     "Archivo local, o URL de YouTube/Google Drive y ~1000 sitios (yt-dlp). "
     "SharePoint/Teams/OneDrive requieren login: descarga manual y usa la ruta."),
]
