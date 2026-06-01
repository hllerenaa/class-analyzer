"""Transcripcion opcional con faster-whisper (local, gratis).

Si la libreria no esta instalada, retorna None y el pipeline sigue sin texto.
"""


def transcribe(video_path, model_size="base", language="es"):
    try:
        from faster_whisper import WhisperModel
    except Exception:
        return None

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _info = model.transcribe(video_path, language=language)
    parts = []
    for seg in segments:
        parts.append(f"[{int(seg.start)//60:02d}:{int(seg.start)%60:02d}] {seg.text.strip()}")
    text = "\n".join(parts)
    return text if text else None
