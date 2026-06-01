# Guía de IA — tokens, instalación y conexión

Cómo generar el token de cada proveedor, instalar Ollama local, y conectarlo
a Class Analyzer. También: instalar la app y cómo funciona.

---

## 0. Resumen de proveedores

| Proveedor | Costo | Token | Dónde se genera |
|-----------|-------|-------|-----------------|
| **Ollama** (local) | 🟢 $0 | No necesita | — (corre en tu PC) |
| **Google Gemini** | 🟢 capa gratis | Sí | aistudio.google.com |
| **DeepSeek** | 💲 muy barato | Sí | platform.deepseek.com |
| **Anthropic Claude** | 💲 de pago | Sí | console.anthropic.com |

Recomendado para "sin costos": **Ollama**.

---

## 1. OLLAMA (local, $0, sin token)

### Instalar
```powershell
# Windows
winget install Ollama.Ollama
```
```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh
```
O descarga manual: https://ollama.com/download

### Arrancar el server
- Windows: arranca solo (app de bandeja). Verifica: abre http://localhost:11434
  → debe decir "Ollama is running".
- Manual / Linux: `ollama serve`

### Descargar un modelo
```bash
ollama pull llama3.2:3b      # ligero, ~2 GB, rápido en CPU
# alternativas:
ollama pull qwen2.5:7b       # mejor calidad, ~4.7 GB, necesita más RAM
ollama pull llama3.1:8b      # ~4.7 GB
```
Ver catálogo: https://ollama.com/library

### Conectar a Class Analyzer
En la pagina **Docs y Tokens** (`/docs-tokens`):
- **Proveedor**: `ollama`
- **API Token**: vacío (deshabilitado)
- **Modelo**: `llama3.2:3b`
- **Base URL**: vacío (usa `http://localhost:11434`). Solo si Ollama está en
  OTRA máquina, pon `http://IP_DE_ESA_MAQUINA:11434`.

Comandos útiles:
```bash
ollama list     # modelos instalados
ollama ps       # modelos cargados en RAM
ollama run llama3.2:3b "hola"   # probar
```

---

## 2. GOOGLE GEMINI (capa gratuita)

### Generar token
1. Entra a **https://aistudio.google.com/app/apikey** con tu cuenta Google.
2. Click **"Create API key"**.
3. Copia la key (empieza con `AIza...`).

### Conectar
- **Proveedor**: `gemini`
- **API Token**: pega la key
- **Modelo**: `gemini-1.5-flash` (rápido/barato) o `gemini-1.5-pro`
- Docs: https://ai.google.dev/gemini-api/docs
- Modelos: https://ai.google.dev/gemini-api/docs/models

---

## 3. DEEPSEEK (barato)

### Generar token
1. Crea cuenta en **https://platform.deepseek.com**.
2. Menú **API keys → "Create new API key"**.
3. Copia la key (`sk-...`).
4. Recarga saldo en Billing (muy bajo costo).

### Conectar
- **Proveedor**: `deepseek`
- **API Token**: pega la key
- **Modelo**: `deepseek-chat`
- Docs: https://api-docs.deepseek.com/
- Precios: https://api-docs.deepseek.com/quick_start/pricing

---

## 4. ANTHROPIC CLAUDE (de pago)

### Generar token
1. Crea cuenta en **https://console.anthropic.com**.
2. **Settings → API Keys → "Create Key"**.
3. Copia la key (`sk-ant-...`).
4. Carga saldo en **Billing** (~$0.02 por clase con Haiku).

### Conectar
- **Proveedor**: `claude`
- **API Token**: pega la key
- **Modelo**: `claude-3-5-haiku-latest` (barato) o `claude-3-5-sonnet-latest`
- Docs: https://docs.anthropic.com/en/api/getting-started
- Modelos: https://docs.anthropic.com/en/docs/about-claude/models

---

## 5. Instalar la aplicación

```bash
# 1) Clonar
git clone https://github.com/hllerenaa/class-analyzer
cd class-analyzer

# 2) ffmpeg (obligatorio)
winget install Gyan.FFmpeg          # Windows
sudo apt install ffmpeg             # Linux

# 3) Entorno + dependencias
python -m venv .venv
.\.venv\Scripts\Activate.ps1        # Windows  (Linux: source .venv/bin/activate)
pip install -r requirements.txt
pip install faster-whisper          # opcional: transcript local

# 4) Correr
uvicorn views:app --reload       # → http://localhost:8000
```
Sin UI (CLI):
```bash
python cli.py "ruta/clase.mp4"                  # solo detección, $0
python cli.py "ruta/clase.mp4" --ai ollama      # + reporte IA local
```

---

## 6. Cómo funciona (flujo)

```
Video clase
   │
   ├─ ffmpeg silencedetect ─► VAD: % de voz del docente
   ├─ ffmpeg frames + diff  ─► playback: ¿hay video corriendo?
   │
   ▼
Motor de reglas  ─► FLAGS (ej. "11 min video, voz 0% → sin clase")
   │
   ├─ (opcional) faster-whisper ─► transcripción de texto
   │
   ▼
IA (Ollama/Claude/Gemini/DeepSeek)  ─► REPORTE pedagógico
```

- Capa de detección = **local, determinista, $0**. Marca la situación.
- IA = solo redacta el reporte sobre texto/métricas. Nunca recibe el video.
- Por eso el costo escala con nº de clases que pasan por IA, no con la duración
  del video. Con Ollama, $0 total.
