# Guía de Ejecución — Class Analyzer

Cómo ejecutar el proyecto **local en Windows** y **en producción**, con todas
las dependencias y requisitos.

---

## 1. Requisitos (qué instalar)

| Dependencia | Para qué | Obligatorio |
|-------------|----------|-------------|
| **Python 3.10–3.13** | Ejecutar la app | ✅ |
| **ffmpeg + ffprobe** | Audio (VAD) y frames (movimiento) | ✅ |
| **pip packages** | fastapi, uvicorn, jinja2, python-multipart, sqlalchemy, psycopg, numpy, Pillow, requests, yt-dlp | ✅ |
| **PostgreSQL** | Guarda config, tokens e historial | ✅ (Docker: `docker-compose.postgres.yml`) |
| **Ollama + modelo** | IA local gratis ($0) | ⬜ opcional |
| **faster-whisper** | Transcripción local | ⬜ opcional |
| Token Claude/Gemini/DeepSeek | IA en la nube | ⬜ alternativa a Ollama |

Dependencias Python (en `requirements.txt`):
```
fastapi, uvicorn[standard], jinja2, python-multipart, sqlalchemy, psycopg[binary], numpy, Pillow, requests, yt-dlp
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

### 2.5 Base de datos PostgreSQL (Docker)
La app guarda config, tokens e historial en **PostgreSQL**. Levantala con Docker:
```powershell
copy credentials.example.json credentials.json   # ajusta password si quieres
docker compose -f docker-compose.postgres.yml up -d
```
`credentials.json` define la conexion (`ip`, `port`, `username`, `password`, `dbname`)
y DEBE coincidir con las variables del compose. Las TABLAS se crean solas al iniciar la app.
> ¿Sin Docker? Instala PostgreSQL nativo, crea el rol y la BD con esos mismos
> datos:  `CREATE ROLE class_analyzer LOGIN PASSWORD 'cambia_esto';`
> `CREATE DATABASE class_analyzer OWNER class_analyzer;`

### 2.6 Ejecutar la interfaz web (FastAPI)
```powershell
uvicorn views:app --reload
```
Abre http://localhost:8000 · Paginas: `/` (Analizador), `/como-usar`, `/docs-tokens`.

### 2.7 Ejecutar por línea de comandos (sin UI)
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

### 2.8 Validar que todo corre
```powershell
ffmpeg -version            # ffmpeg OK
ollama list                # modelos instalados
curl http://localhost:11434/api/version   # Ollama vivo
docker compose -f docker-compose.postgres.yml ps   # PostgreSQL arriba
# la app: navegador en http://localhost:8000
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
- Servicio persistente: **systemd** (`class-analyzer.service`) ejecutando
  `uvicorn views:app --host 0.0.0.0 --port 8000` (o `gunicorn -k uvicorn.workers.UvicornWorker`).
- Reverse proxy: **Nginx**.
- HTTPS gratis: **certbot** (Let's Encrypt).

### 4.2 Windows Server
- Servicio 24/7: **NSSM** apuntando a `uvicorn views:app --host 0.0.0.0 --port 8000`.
- Reverse proxy + HTTPS: **IIS (ARR + URL Rewrite)** o **Caddy**.
- Ollama se instala como servicio Windows (auto-arranque).

### 4.3 Docker (portátil)
```bash
docker compose up -d --build
docker compose exec ollama ollama pull llama3.2:3b
```
Incluye app + Ollama. Ver `Dockerfile` y `docker-compose.yml`.

> ¿Ollama en un servidor aparte (o con GPU) y conectarlo por **Base URL**?
> Guia dedicada en `DEPLOYMENT.md` §7 (Docker, acceso remoto seguro, firewall).

---

## 5. Estructura del proyecto (MVC)

```
class-analyzer/
  views/              VISTAS/URLs (FastAPI). App = views:app
    __init__.py         crea `app`, monta /static, incluye los routers
    base.py             plantillas Jinja2 + rutas base (compartido)
    analizador.py       ROUTER: /  y  /analizar
    paginas.py          ROUTER: /como-usar, /docs-tokens, /guardar-credenciales
    historial.py        ROUTER: /historial/...
    content.py          CONTENIDO (textos, links docs, PROVIDER_INFO, HOWTO_*) — datos puros
  models/             MODELO ORM (SQLAlchemy)
    db.py               engine PostgreSQL, sesiones, Base, credenciales, create_all
    setting.py          modelo Setting
    provider_cred.py    modelo ProviderCred
    history.py          modelo History
  templates/          PLANTILLAS Jinja2 (.html): base, index, resultados,
                      como_usar, docs_tokens, historial_detalle, error
  static/css/styles.css  ESTILO (todo el diseno en un solo CSS, nivel raiz)
  cli.py              CONTROLADOR (línea de comandos)
  analyzer/           LÓGICA de dominio
    store.py            DAO sobre el ORM (config, tokens, historial)
    downloader.py       descarga URL (yt-dlp)
    ffmpeg_util.py      localizar ffmpeg
    video_probe.py      metadatos
    audio.py            VAD por silencio
    motion.py           playback por movimiento
    rules.py            motor de flags (dominio)
    transcribe.py       whisper (opcional)
    ai_providers.py     Claude/Gemini/DeepSeek/Ollama
    pipeline.py         orquestación
  credentials.json    conexion PostgreSQL (ip/port/username/password/dbname) — ignorado en git
  credentials.example.json  plantilla de credenciales
  requirements.txt    dependencias
  Dockerfile / docker-compose.yml / docker-compose.ollama.yml / docker-compose.postgres.yml
  README.md / EJECUTAR.md / DEPLOYMENT.md / GUIA_IA.md
```

- **Vistas/URLs** = paquete `views/` (un **router** por seccion) + `templates/*.html`.
- **Router de rutas** = `views/analizador.py`, `views/paginas.py`, `views/historial.py`
  (cada uno expone `router = APIRouter()`); `views/__init__.py` los ensambla en `app`.
- **Estilo** = `static/css/styles.css` (un solo archivo, a nivel raiz).
- **Contenido** = `views/content.py` → `PROVIDER_INFO`, `MODEL_HINTS`, `HOWTO_*`.
- **Modelo** = paquete `models/` (SQLAlchemy ORM, un archivo por entidad, crea el esquema) + `analyzer/store.py` (DAO).
- **CLI** = `cli.py` (terminal, sin cambios).

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

