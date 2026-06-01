"""Orquesta: probe -> audio VAD -> motion -> reglas -> (IA opcional)."""
from . import ffmpeg_util, video_probe, audio as audio_mod, motion as motion_mod
from . import rules, ai_providers


def build_prompt(meta, summary, flags, transcript):
    lines = [
        "Eres evaluador pedagogico. Analiza esta grabacion de clase y detecta "
        "debilidades. Se concreto y accionable.",
        "",
        "METRICAS (detectadas automaticamente, sin IA):",
        f"- Duracion: {summary['duration_min']} min",
        f"- Tiempo con voz/audio activo: {round(summary['speech_ratio']*100)}%",
        f"- Tiempo con playback de video en pantalla: {round(summary['playback_ratio']*100)}%",
        f"- Segmentos marcados: {summary['num_flags']} "
        f"({summary['flagged_minutes']} min)",
        "",
        "SEGMENTOS SOSPECHOSOS:",
    ]
    if flags:
        for f in flags:
            lines.append(f"- {f['label']}")
    else:
        lines.append("- (ninguno automatico)")
    lines += [
        "",
        "TRANSCRIPCION (si disponible):",
        (transcript[:6000] if transcript else "(no disponible)"),
        "",
        "Entrega un reporte en espanol con: 1) Resumen ejecutivo, "
        "2) Debilidades detectadas (con minutos), "
        "3) Si hubo 'video compartido sin clase' confirmalo o descartalo, "
        "4) Recomendaciones para el docente.",
    ]
    return "\n".join(lines)


def analyze(video_path, cfg, want_transcript=False, ai_enabled=True, log=print):
    ffmpeg, ffprobe = ffmpeg_util.resolve(cfg.get("ffmpeg_dir", ""))
    thr = cfg["thresholds"]

    log("Probe metadatos...")
    meta = video_probe.probe(ffprobe, video_path)
    duration = meta["duration"]

    log("Analisis de audio (VAD por silencio)...")
    audio = audio_mod.analyze_audio(
        ffmpeg, video_path, duration,
        noise_db=thr["silence_noise_db"],
        min_dur=thr["silence_min_dur"],
    )

    log("Analisis de movimiento (playback de video)...")
    diffs = motion_mod.motion_per_second(ffmpeg, video_path)
    playback = motion_mod.playback_per_second(diffs, thr["motion_playback"])

    log("Aplicando reglas...")
    flags = rules.detect_flags(duration, audio["speech_per_sec"], playback, thr)
    summary = rules.summarize(duration, audio, playback, flags)

    transcript = None
    if want_transcript:
        log("Transcribiendo (faster-whisper si esta instalado)...")
        from . import transcribe as tr
        transcript = tr.transcribe(video_path)

    report = None
    if ai_enabled:
        log(f"Generando reporte IA via '{cfg.get('provider')}'...")
        prompt = build_prompt(meta, summary, flags, transcript)
        report = ai_providers.generate_report(
            cfg.get("provider"), cfg.get("api_key"),
            cfg.get("model"), cfg.get("base_url"), prompt,
        )

    return {
        "meta": meta,
        "summary": summary,
        "flags": flags,
        "transcript": transcript,
        "report": report,
        "motion": diffs,
        "playback": playback,
        "speech": audio["speech_per_sec"],
    }
