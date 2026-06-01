# Guía de Ejecución — Class Analyzer

Cómo ejecutar el proyecto **local en Windows** y **en producción**, con todas
las dependencias y requisitos.

---

## 1. Requisitos (qué instalar)

| Dependencia | Para qué | Obligatorio |
|-------------|----------|-------------|
| **Python 3.10–3.13** | Ejecutar la app | ✅ |
| **ffmpeg + ffprobe** | Audio (VAD) y frames (movimiento) | ✅ |
| **pip packages** | streamlit, numpy, Pillow, requests, yt-dlp | ✅ |
| **Ollama + modelo** | IA local gratis ($0) | ⬜ opcional |
| **faster-whisper** | Transcripción local | ⬜ opcional |
| Token Claude/Gemini/DeepSeek | IA en la nube | ⬜ alternativa a Ollama |

Dependencias Python (en `requirements.txt`):
```
streamlit, numpy, Pillow, requests, yt-dlp
# opcional: faster-whisper
```

---

## 2. Ejecutar LOCAL en Windows (paso a paso)

### 2.1 Instalar ffmpeg
```powershell
winget install Gyan.FFmpeg
```
> Cierra y reabre la terminal para refrescar el PATH. La app igual lo
> autodetecta aunque no esté en PATH (busca la instalación de winget).

### 2.2 Obtener el código
```powershell
git clone https://github.com/hllerenaa/class-analyzer
cd class-analyzer
```

### 2.3 Entorno virtual + dependencias
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# opcional (transcript):
pip install faster-whisper
```
> Si PowerShell bloquea el script de activación:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

### 2.4 (Opcional) IA local gratis con Ollama
```powershell
winget install Ollama.Ollama
ollama pull llama3.2:3b
```
El servidor queda en `http://localhost:11434` (arranca solo).

### 2.5 Ejecutar la interfaz web
```powershell
streamlit run app.py
```
Abre http://localhost:8501

### 2.6 Ejecutar por línea de comandos (sin UI)
```powershell
# solo detección (sin IA, $0)
python cli.py "C:\ruta\clase.mp4"

# detección + reporte IA local
python cli.py "C:\ruta\clase.mp4" --ai ollama --model llama3.2:3b

# desde una URL (YouTube / Drive)
python cli.py "https://www.youtube.com/watch?v=XXXX" --ai ollama

# IA en la nube con token
python cli.py "C:\ruta\clase.mp4" --ai gemini --key TU_TOKEN
```

### 2.7 Validar que todo corre
```powershell
ffmpeg -version            # ffmpeg OK
ollama list                # modelos instalados
curl http://localhost:11434/api/version   # Ollama vivo
# la app: navegador en http://localhost:8501
```

---

## 3. Fuentes de video soportadas

| Fuente | Soporte |
|--------|---------|
| Archivo local (ruta o subida) | ✅ |
| YouTube | ✅ (yt-dlp) |
| Google Drive (link compartido público) | ✅ (yt-dlp) |
| SharePoint / Teams / OneDrive | ⚠️ requieren login → descarga manual y usa ruta local |

---

## 4. Ejecutar en PRODUCCIÓN (resumen)

> Detalle completo (servicios, proxy, HTTPS, seguridad) en **`DEPLOYMENT.md`**.

### 4.1 Linux (recomendado)
```bash
sudo apt install -y ffmpeg python3-venv nginx
curl -fsSL https://ollama.com/install.sh | sh
cd /opt && git clone https://github.com/hllerenaa/class-analyzer && cd class-analyzer
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt faster-whisper
ollama pull llama3.2:3b
```
- Servicio persistente: **systemd** (`class-analyzer.service`).
- Reverse proxy + WebSockets: **Nginx**.
- HTTPS gratis: **certbot** (Let's Encrypt).

### 4.2 Windows Server
- Servicio 24/7: **NSSM** apuntando a `streamlit run app.py`.
- Reverse proxy + HTTPS: **IIS (ARR + URL Rewrite)** o **Caddy**.
- Ollama se instala como servicio Windows (auto-arranque).

### 4.3 Docker (portátil)
```bash
docker compose up -d --build
docker compose exec ollama ollama pull llama3.2:3b
```
Incluye app + Ollama. Ver `Dockerfile` y `docker-compose.yml`.

---

## 5. Estructura del proyecto (MVC)

```
class-analyzer/
  app.py              CONTROLADOR (Streamlit): conecta vistas + modelo
  cli.py              CONTROLADOR (línea de comandos)
  ui/                 PRESENTACIÓN
    templates.py        PLANTILLAS (texto, markdown, constantes)
    views.py            VISTAS (funciones view_* que renderizan)
  analyzer/           MODELO / lógica
    downloader.py       descarga URL (yt-dlp)
    ffmpeg_util.py      localizar ffmpeg
    video_probe.py      metadatos
    audio.py            VAD por silencio
    motion.py           playback por movimiento
    rules.py            motor de flags (dominio)
    transcribe.py       whisper (opcional)
    ai_providers.py     Claude/Gemini/DeepSeek/Ollama
    pipeline.py         orquestación
  requirements.txt    dependencias
  Dockerfile / docker-compose.yml
  README.md / EJECUTAR.md / DEPLOYMENT.md / GUIA_IA.md
```

- **Vistas** = `ui/views.py` → funciones `view_header`, `view_sidebar_config`,
  `view_input`, `view_results`, `view_provider_help`.
- **Plantillas** = `ui/templates.py` → `APP_TITLE`, `HELP_MD`, `PROVIDER_INFO`,
  `MODEL_HINTS`.
- **Controlador** = `app.py` (web) y `cli.py` (terminal).
- **Modelo** = paquete `analyzer/`.

---

## 6. Problemas comunes

| Síntoma | Causa / solución |
|---------|------------------|
| `No se encontro ffmpeg` | Instala `winget install Gyan.FFmpeg` o define la carpeta en el sidebar |
| Ollama "Read timed out" 1ª vez | Carga del modelo a RAM. Reintenta; ya se subió el timeout a 600s |
| `UnicodeEncodeError` en consola | Usa `set PYTHONIOENCODING=utf-8` (el CLI ya lo fuerza) |
| URL SharePoint falla | Requiere login; descarga manual y usa la ruta local |
| Activación venv bloqueada | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
```

