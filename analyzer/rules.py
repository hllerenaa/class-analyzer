"""Motor de reglas: combina senales y emite flags (sin IA)."""


def _fmt(sec):
    sec = int(sec)
    return f"{sec // 60:02d}:{sec % 60:02d}"


def detect_flags(duration, speech_per_sec, playback_per_sec, thr):
    """Detecta segmentos sospechosos.

    Regla principal 'video compartido sin enseñar':
      run contiguo donde playback=True y speech bajo localmente,
      con duracion >= min_flag_minutes.
    """
    n = int(min(len(speech_per_sec), len(playback_per_sec)))
    min_run = int(thr["min_flag_minutes"] * 60)
    low_ratio = thr["speech_ratio_low"]

    flags = []
    i = 0
    while i < n:
        if playback_per_sec[i]:
            j = i
            speak = 0
            total = 0
            while j < n and playback_per_sec[j]:
                total += 1
                if speech_per_sec[j]:
                    speak += 1
                j += 1
            local_ratio = speak / total if total else 1.0
            if total >= min_run and local_ratio < low_ratio:
                flags.append({
                    "type": "video_compartido_sin_clase",
                    "start": i,
                    "end": j,
                    "duration_sec": total,
                    "speech_ratio": round(local_ratio, 3),
                    "label": (
                        f"Playback de video {_fmt(i)}–{_fmt(j)} "
                        f"({total // 60} min) con voz docente "
                        f"{round(local_ratio * 100)}% → posible video sin clase"
                    ),
                })
            i = j
        else:
            i += 1
    return flags


def summarize(duration, audio, playback_per_sec, flags):
    n = int(min(len(audio["speech_per_sec"]), len(playback_per_sec)))
    play_secs = sum(1 for x in playback_per_sec[:n] if x)
    return {
        "duration_min": round(duration / 60, 1),
        "speech_ratio": round(audio["speech_ratio"], 3),
        "playback_ratio": round(play_secs / n, 3) if n else 0.0,
        "num_flags": len(flags),
        "flagged_minutes": round(sum(f["duration_sec"] for f in flags) / 60, 1),
    }
