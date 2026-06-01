"""VAD barata via ffmpeg silencedetect (sin ML/torch).

Devuelve por-segundo si hay voz/audio activo, y ratio de actividad.
"""
import re
import subprocess


def _run_silencedetect(ffmpeg, video_path, noise_db, min_dur):
    cmd = [
        ffmpeg, "-hide_banner", "-nostats", "-i", video_path,
        "-af", f"silencedetect=noise={noise_db}dB:d={min_dur}",
        "-f", "null", "-",
    ]
    # silencedetect escribe en stderr
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.stderr


def analyze_audio(ffmpeg, video_path, duration, noise_db=-30, min_dur=0.5):
    """Retorna dict con:
      speech_per_sec: lista bool por segundo (True = audio/voz activa)
      speech_ratio: fraccion del tiempo con actividad de audio
      silence_segments: lista (start, end)
    """
    stderr = _run_silencedetect(ffmpeg, video_path, noise_db, min_dur)

    starts = [float(m) for m in re.findall(r"silence_start:\s*([0-9.]+)", stderr)]
    ends = [float(m) for m in re.findall(r"silence_end:\s*([0-9.]+)", stderr)]

    # Emparejar starts/ends en orden
    silence = []
    ei = 0
    for st in starts:
        end = duration
        while ei < len(ends) and ends[ei] < st:
            ei += 1
        if ei < len(ends):
            end = ends[ei]
            ei += 1
        silence.append((st, end))

    n = max(1, int(round(duration)))
    speech = [True] * n  # por defecto hay audio; marcamos silencios como False
    for (st, en) in silence:
        a = max(0, int(st))
        b = min(n, int(en) + 1)
        for s in range(a, b):
            speech[s] = False

    ratio = sum(1 for x in speech if x) / n
    return {
        "speech_per_sec": speech,
        "speech_ratio": ratio,
        "silence_segments": silence,
    }
