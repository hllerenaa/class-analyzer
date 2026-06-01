# Class Analyzer

Detecta debilidades en grabaciones de clase. Caso clave: **>10 min de video
compartido donde el docente no dio clase activa**.

## Como funciona (2 capas)

1. **Deteccion local (sin IA, costo $0)** — ffmpeg + numpy:
   - VAD por silencio (`silencedetect`) → cuanto habla el docente.
   - Movimiento entre frames → detecta playback de video en pantalla.
   - Motor de reglas → marca segmentos sospechosos.
2. **IA (pluggable, opcional)** — solo redacta el reporte sobre las senales
   ya detectadas. Provider configurable con un token:
   `claude` | `gemini` | `deepseek` | `ollama` (local/gratis).

El video **nunca** se manda a la IA (caro). Solo metricas + transcript de texto.

## Instalar

```
pip install -r requirements.txt
# ffmpeg requerido: winget install Gyan.FFmpeg
# (opcional) transcript local: pip install faster-whisper
```

## Usar

UI web:
```
streamlit run app.py
```

CLI (solo deteccion, sin IA):
```
python cli.py "C:\ruta\clase.mp4"
```

CLI con IA:
```
python cli.py "C:\ruta\clase.mp4" --ai claude --key TU_TOKEN --model claude-3-5-haiku-latest
python cli.py "C:\ruta\clase.mp4" --ai ollama   # local, sin token
```

## Costo

- Deteccion capa-1: **$0** (local).
- IA: solo texto. ~12k tokens/clase de 1h. Haiku ≈ $0.02/clase
  → ~$2 por 100 clases/mes. Ollama local = $0.

## Umbrales (ajustables en UI o config.example.json)

| Param | Default | Que hace |
|-------|---------|----------|
| `min_flag_minutes` | 10 | Duracion minima de un segmento para marcarlo |
| `motion_playback` | 12.0 | Umbral de movimiento = video corriendo |
| `speech_ratio_low` | 0.15 | Voz docente por debajo de esto = sospechoso |
| `silence_noise_db` | -30 | Nivel para considerar silencio |
