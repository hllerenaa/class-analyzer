# Despliegue en Producción — Class Analyzer

Guía completa para levantar el proyecto en **Windows** y **Linux**.
Cubre instalación, servicio persistente, reverse proxy, Docker y seguridad.

Arquitectura en producción:

```
[Usuario] → HTTPS → [Nginx/IIS reverse proxy] → [FastAPI/uvicorn :8000]
                                                      │
                              ┌──────────────┬────────┼────────┬──────────────┐
                              ▼              ▼        ▼        ▼              ▼
                        [ffmpeg]   [faster-whisper] [Ollama] [PostgreSQL]  (LLM nube
                        (local)     (local, CPU)    :11434   :5432          opcional)
                                                    ($0)     (config/tokens/historial)
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
uvicorn views:app --host 0.0.0.0 --port 8000
```

### 1.3 Servicio persistente con NSSM

Para que corra 24/7 sin sesión abierta:

```powershell
winget install NSSM.NSSM   # o descarga de nssm.cc
nssm install ClassAnalyzer
```
En el diálogo NSSM:
- **Path**: `C:\Users\aaron\class-analyzer\.venv\Scripts\python.exe`
- **Arguments**: `-m uvicorn views:app --host 127.0.0.1 --port 8000`
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
3. En el sitio, regla de reescritura inversa hacia `http://127.0.0.1:8000/`.
4. HTTP normal (FastAPI no requiere WebSockets); sube `maxAllowedContentLength` para subidas grandes.
5. Certificado: **win-acme** (`wacs.exe`) para Let's Encrypt gratis, o cert corporativo.

Alternativa más simple en Windows: usar **Caddy** (HTTPS automático):
```
class.tudominio.com {
    reverse_proxy 127.0.0.1:8000
}
```

### 1.5 Firewall

```powershell
New-NetFirewallRule -DisplayName "ClassAnalyzer HTTPS" -Direction Inbound -LocalPort 443 -Protocol TCP -Action Allow
# NO abrir 8000 ni 11434 al exterior: solo localhost.
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
Description=Class Analyzer (FastAPI/uvicorn)
After=network.target ollama.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/class-analyzer
Environment=PYTHONIOENCODING=utf-8
ExecStart=/opt/class-analyzer/.venv/bin/uvicorn views:app \
  --host 127.0.0.1 --port 8000
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
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 3600s;   # análisis largos (request sincrono)
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
EXPOSE 8000
ENV PYTHONIOENCODING=utf-8
CMD ["uvicorn", "views:app", "--host", "0.0.0.0", "--port", "8000"]
```

`docker-compose.yml` (app + Ollama + PostgreSQL) — ver el archivo en el repo.
La app recibe la conexion a la BD por variables `DB_*` (override de `credentials.json`):
```yaml
  app:
    build: .
    depends_on:
      db: { condition: service_healthy }
      ollama: { condition: service_started }
    environment:
      - DB_IP=db
      - DB_PORT=5432
      - DB_USERNAME=class_analyzer
      - DB_PASSWORD=cambia_esto
      - DB_NAME=class_analyzer
    ports:
      - "127.0.0.1:8000:8000"
```
> Composes adicionales: `docker-compose.postgres.yml` (solo BD) y
> `docker-compose.ollama.yml` (solo Ollama) para servidores dedicados.

Levantar:
```bash
docker compose up -d --build
docker compose exec ollama ollama pull llama3.2:3b
```

> En la pagina **Docs y Tokens** usa Base URL `http://ollama:11434` cuando corras en compose.
> GPU: añade `deploy.resources.reservations.devices` (NVIDIA) al servicio ollama.

---

## 4. Seguridad

- **Nunca** expongas Ollama (`11434`) ni FastAPI (`8000`) directo a internet — solo `127.0.0.1`, detrás del proxy.
- Autenticación: FastAPI no trae login por defecto. Añade auth en el proxy:
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
  (**Celery + Redis** o **RQ**) con workers separados; FastAPI solo encola y
  muestra estado.
- Almacenamiento: object storage (MinIO local = $0, o S3) para videos/reportes.
- Varios workers → balancear con Nginx `upstream`.
- LLM bajo carga: Ollama con GPU, o servir el modelo con vLLM.
- Métricas: Prometheus + Grafana sobre el worker y la cola.

---

## 7. Ollama en un servidor con Docker (y conectarlo a la app)

Levanta Ollama en un servidor (mismo host o uno dedicado/GPU) y apunta la app a
él vía **Base URL**. La app solo manda texto al endpoint `/api/...` de Ollama.

### 7.1 Levantar Ollama (solo Ollama) con Docker

```bash
# CPU
docker run -d --name ollama \
  -p 127.0.0.1:11434:11434 \
  -v ollama:/root/.ollama \
  --restart unless-stopped \
  ollama/ollama:latest

# Descargar el modelo (una vez)
docker exec -it ollama ollama pull llama3.2:3b
```

GPU NVIDIA (requiere `nvidia-container-toolkit` en el host):
```bash
docker run -d --name ollama --gpus all \
  -p 127.0.0.1:11434:11434 \
  -v ollama:/root/.ollama \
  --restart unless-stopped \
  ollama/ollama:latest
```

`docker-compose.yml` (Ollama solo):
```yaml
services:
  ollama:
    image: ollama/ollama:latest
    restart: unless-stopped
    volumes:
      - ollama:/root/.ollama
    ports:
      - "127.0.0.1:11434:11434"   # solo localhost; ver 7.3 para acceso remoto
    # GPU: descomenta
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - capabilities: ["gpu"]
volumes:
  ollama:
```

Probar que vive:
```bash
curl http://127.0.0.1:11434/api/version
docker exec -it ollama ollama list
```

### 7.2 Conectar la app a este Ollama

En la pagina **Docs y Tokens** de la app:
- Proveedor: `ollama`
- Modelo: `llama3.2:3b` (o el que hayas hecho `pull`)
- **Base URL**: la del servidor Ollama
  - Mismo host: `http://127.0.0.1:11434`
  - App en Docker compose junto a Ollama: `http://ollama:11434` (nombre del servicio)
  - Servidor remoto: `http://IP_DEL_SERVIDOR:11434` (ver 7.3 — protégelo)
- API Token: vacio (Ollama no usa token).

Guarda → marca como proveedor activo. El Analizador ya usara ese endpoint.

### 7.3 Exponerlo a otra maquina de forma SEGURA

Ollama **no trae autenticacion**. No publiques `11434` abierto a internet.
Opciones (de mas a menos recomendada):

1. **Tunel SSH** desde la maquina de la app (lo mas simple y seguro):
   ```bash
   ssh -N -L 11434:127.0.0.1:11434 usuario@servidor-ollama
   # ahora en la app: Base URL = http://127.0.0.1:11434
   ```
2. **Red privada** (VPN/WireGuard o red interna del datacenter): publica
   `11434` solo en esa interfaz y usa la IP privada del servidor.
3. **Reverse proxy con auth + HTTPS** (Nginx/Caddy) delante de Ollama:
   - Caddy:
     ```
     ollama.tudominio.com {
         basic_auth { usuario HASH_BCRYPT }
         reverse_proxy 127.0.0.1:11434
     }
     ```
   - En la app, Base URL = `https://ollama.tudominio.com`.
   > Nota: Ollama no procesa cabeceras de auth; la auth la pone el proxy.
     Si el proxy exige `Authorization`, este cliente simple no la envia: usa
     preferentemente el tunel SSH o la red privada.

### 7.4 Firewall (no abrir Ollama al mundo)

```bash
# Linux (ufw): permitir solo desde la IP de la app (red privada)
sudo ufw allow from 10.0.0.5 to any port 11434 proto tcp
sudo ufw deny 11434
```

> Resumen: Ollama escucha en `127.0.0.1` por defecto. Para acceso remoto, NO lo
> abras directo: tunel SSH o red privada. La app se conecta cambiando solo la
> **Base URL** en *Docs y Tokens*.


---

## 8. PostgreSQL (base de datos) con Docker

La app guarda **config, tokens de IA e historial** en PostgreSQL. La conexion
se define en `credentials.json` (raiz del proyecto) o por variables `DB_*`.

`credentials.json`:
```json
{
  "ip": "127.0.0.1",
  "port": 5432,
  "username": "class_analyzer",
  "password": "cambia_esto",
  "dbname": "class_analyzer"
}
```
> Es secreto -> esta en `.gitignore`. Parte de `credentials.example.json`.
> Overrides por entorno: `DB_IP`, `DB_PORT`, `DB_USERNAME`, `DB_PASSWORD`, `DB_NAME`
> (utiles en contenedores). Estos valores DEBEN coincidir con los del compose.

### 8.1 Levantar solo la BD
```bash
docker compose -f docker-compose.postgres.yml up -d
# comprobar:
docker compose -f docker-compose.postgres.yml exec db \
  psql -U class_analyzer -d class_analyzer -c "\dt"
```
La imagen crea la base `POSTGRES_DB` en el primer arranque; las **tablas** las
crea la app sola con `store.init()` al iniciar (idempotente).

### 8.2 PostgreSQL nativo (sin Docker)
```sql
CREATE ROLE class_analyzer LOGIN PASSWORD 'cambia_esto';
CREATE DATABASE class_analyzer OWNER class_analyzer;
```
Ajusta `credentials.json` con esos datos.

### 8.3 BD en un servidor remoto
Como Ollama (§7.3): NO expongas `5432` a internet. Usa **tunel SSH**
(`ssh -N -L 5432:127.0.0.1:5432 user@servidor-bd`, luego `ip: 127.0.0.1`) o una
**red privada/VPN** con la IP interna del servidor en `credentials.json`.

### 8.4 Backup / restore
```bash
# backup
docker compose -f docker-compose.postgres.yml exec db \
  pg_dump -U class_analyzer class_analyzer > backup.sql
# restore
docker compose -f docker-compose.postgres.yml exec -T db \
  psql -U class_analyzer -d class_analyzer < backup.sql
```

> El dato persiste en el volumen `pgdata`. Borrarlo (`docker volume rm`) elimina
> config, tokens e historial.
