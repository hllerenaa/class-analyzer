# Despliegue en Producción — Class Analyzer

Guía completa para levantar el proyecto en **Windows** y **Linux**.
Cubre instalación, servicio persistente, reverse proxy, Docker y seguridad.

Arquitectura en producción:

```
[Usuario] → HTTPS → [Nginx/IIS reverse proxy] → [Streamlit :8501]
                                                      │
                                    ┌─────────────────┼──────────────────┐
                                    ▼                 ▼                  ▼
                              [ffmpeg]        [faster-whisper]    [Ollama :11434]
                              (local)          (local, CPU)       (LLM local, $0)
```

Todo es **local / $0 recurrente**. Sin dependencias de nube.

---

## 0. Requisitos comunes

| Componente | Versión | Uso |
|-----------|---------|-----|
| Python | 3.10–3.13 | App |
| ffmpeg + ffprobe | ≥ 6.x | Audio/movimiento |
| Ollama | ≥ 0.3 | Reporte IA local (opcional) |
| faster-whisper | ≥ 1.0 | Transcript local (opcional) |
| RAM | 8 GB mín (16 GB con LLM 7B) | — |
| Disco | ~6 GB (modelos) | — |

---

## 1. WINDOWS (producción)

### 1.1 Instalar dependencias

```powershell
# ffmpeg
winget install Gyan.FFmpeg
# Ollama (IA local)
winget install Ollama.Ollama
# Python deps
cd C:\Users\aaron\class-analyzer
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install faster-whisper        # transcript opcional
```

Descargar modelo LLM (una vez):
```powershell
ollama serve            # en otra terminal, o corre como servicio (1.5)
ollama pull llama3.2:3b # ~2 GB, rápido en CPU
```

### 1.2 Prueba manual

```powershell
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### 1.3 Servicio persistente con NSSM

Para que corra 24/7 sin sesión abierta:

```powershell
winget install NSSM.NSSM   # o descarga de nssm.cc
nssm install ClassAnalyzer
```
En el diálogo NSSM:
- **Path**: `C:\Users\aaron\class-analyzer\.venv\Scripts\python.exe`
- **Arguments**: `-m streamlit run app.py --server.port 8501 --server.address 127.0.0.1`
- **Startup directory**: `C:\Users\aaron\class-analyzer`
- Pestaña *I/O*: redirige stdout/stderr a un log.

Arrancar:
```powershell
nssm start ClassAnalyzer
```

Ollama ya se instala como servicio Windows (auto-start). Verifica:
```powershell
Get-Service Ollama
```

### 1.4 Reverse proxy + HTTPS (IIS)

1. Instala IIS + módulos **URL Rewrite** y **Application Request Routing (ARR)**.
2. Habilita proxy en ARR (`Server Farms` o `Application Request Routing → Proxy → Enable`).
3. En el sitio, regla de reescritura inversa hacia `http://127.0.0.1:8501/`.
4. Streamlit usa WebSockets → en `web.config` permite `Upgrade`/`Connection` headers.
5. Certificado: **win-acme** (`wacs.exe`) para Let's Encrypt gratis, o cert corporativo.

Alternativa más simple en Windows: usar **Caddy** (HTTPS automático):
```
class.tudominio.com {
    reverse_proxy 127.0.0.1:8501
}
```

### 1.5 Firewall

```powershell
New-NetFirewallRule -DisplayName "ClassAnalyzer HTTPS" -Direction Inbound -LocalPort 443 -Protocol TCP -Action Allow
# NO abrir 8501 ni 11434 al exterior: solo localhost.
```

---

## 2. LINUX (producción — recomendado)

### 2.1 Instalar dependencias (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y ffmpeg python3-venv python3-pip nginx
# Ollama
curl -fsSL https://ollama.com/install.sh | sh
# App
cd /opt
sudo git clone <repo> class-analyzer   # o copia los archivos
cd class-analyzer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install faster-whisper
# Modelo LLM
ollama pull llama3.2:3b
```

### 2.2 Servicio systemd — App

`/etc/systemd/system/class-analyzer.service`:
```ini
[Unit]
Description=Class Analyzer (Streamlit)
After=network.target ollama.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/class-analyzer
Environment=PYTHONIOENCODING=utf-8
ExecStart=/opt/class-analyzer/.venv/bin/streamlit run app.py \
  --server.port 8501 --server.address 127.0.0.1 \
  --server.headless true
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Ollama trae su propio service (`ollama.service`) al instalar con el script.

Activar:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now class-analyzer
sudo systemctl status class-analyzer
```

### 2.3 Reverse proxy Nginx + WebSockets

`/etc/nginx/sites-available/class-analyzer`:
```nginx
server {
    listen 80;
    server_name class.tudominio.com;

    client_max_body_size 2G;   # videos grandes

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 3600s;   # análisis largos
    }
}
```
```bash
sudo ln -s /etc/nginx/sites-available/class-analyzer /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 2.4 HTTPS gratis (Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d class.tudominio.com
# Renovación automática ya queda en cron/systemd-timer.
```

---

## 3. Docker (portable, Windows o Linux)

`Dockerfile`:
```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt faster-whisper
COPY . .
EXPOSE 8501
ENV PYTHONIOENCODING=utf-8
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
```

`docker-compose.yml` (app + Ollama):
```yaml
services:
  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama:/root/.ollama
    ports:
      - "127.0.0.1:11434:11434"

  app:
    build: .
    depends_on:
      - ollama
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    ports:
      - "127.0.0.1:8501:8501"

volumes:
  ollama:
```

Levantar:
```bash
docker compose up -d --build
docker compose exec ollama ollama pull llama3.2:3b
```

> En `app.py` usa Base URL `http://ollama:11434` cuando corras en compose.
> GPU: añade `deploy.resources.reservations.devices` (NVIDIA) al servicio ollama.

---

## 4. Seguridad

- **Nunca** expongas Ollama (`11434`) ni Streamlit (`8501`) directo a internet — solo `127.0.0.1`, detrás del proxy.
- Autenticación: Streamlit no trae login. Añade auth en el proxy:
  - Nginx: `auth_basic` + `htpasswd`, o **oauth2-proxy** (Google/SSO).
- Tokens de IA en nube (si algún día usas Claude/Gemini): variables de entorno o secret manager, **no** en el repo. Modo $0 con Ollama no necesita tokens.
- Sube los videos a almacenamiento temporal y bórralos tras el análisis (privacidad de clases).
- HTTPS obligatorio (certbot / Caddy / win-acme).
- Aísla por `User=` sin privilegios (systemd) o cuenta de servicio dedicada (Windows).

---

## 5. Operación

| Tarea | Comando |
|-------|---------|
| Logs app (Linux) | `journalctl -u class-analyzer -f` |
| Logs app (Windows NSSM) | archivo de I/O configurado |
| Reiniciar app | `systemctl restart class-analyzer` / `nssm restart ClassAnalyzer` |
| Estado Ollama | `ollama ps` |
| Modelos instalados | `ollama list` |
| Actualizar deps | `pip install -U -r requirements.txt` |

---

## 6. Escalado (a futuro)

- Análisis es CPU-pesado (ffmpeg + Whisper). Para muchos videos: cola async
  (**Celery + Redis** o **RQ**) con workers separados; Streamlit solo encola y
  muestra estado.
- Almacenamiento: object storage (MinIO local = $0, o S3) para videos/reportes.
- Varios workers → balancear con Nginx `upstream`.
- LLM bajo carga: Ollama con GPU, o servir el modelo con vLLM.
- Métricas: Prometheus + Grafana sobre el worker y la cola.
```

