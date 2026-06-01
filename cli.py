"""CLI rapido para probar capa-1 (deteccion local) sin UI ni IA.

Uso:
  python cli.py "C:\\ruta\\clase.mp4"
  python cli.py "C:\\ruta\\clase.mp4" --ai claude --key sk-... --model claude-3-5-haiku-latest
"""
import sys
import json
import argparse

# Consola Windows: forzar UTF-8 para caracteres como '→'
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from analyzer import pipeline, downloader


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video", help="ruta local o URL (YouTube/Drive)")
    ap.add_argument("--ai", default=None, help="claude|gemini|deepseek|ollama")
    ap.add_argument("--key", default="")
    ap.add_argument("--model", default="")
    ap.add_argument("--base-url", default="")
    ap.add_argument("--ffmpeg-dir", default="")
    ap.add_argument("--min-flag-min", type=int, default=10)
    ap.add_argument("--transcript", action="store_true")
    args = ap.parse_args()

    cfg = {
        "ffmpeg_dir": args.ffmpeg_dir,
        "provider": args.ai or "ollama",
        "model": args.model,
        "api_key": args.key,
        "base_url": args.base_url,
        "thresholds": {
            "min_flag_minutes": args.min_flag_min,
            "motion_playback": 12.0,
            "speech_ratio_low": 0.15,
            "silence_noise_db": -30,
            "silence_min_dur": 0.5,
        },
    }

    log = lambda m: print("  ..", m)
    video_path = downloader.resolve_source(args.video, log=log)
    res = pipeline.analyze(
        video_path, cfg,
        want_transcript=args.transcript,
        ai_enabled=bool(args.ai),
        log=log,
    )

    print("\n=== METRICAS ===")
    print(json.dumps(res["summary"], indent=2, ensure_ascii=False))
    print("\n=== FLAGS ===")
    for f in res["flags"]:
        print(" -", f["label"])
    if not res["flags"]:
        print(" (ninguno)")
    if res["report"]:
        print("\n=== REPORTE IA ===\n")
        print(res["report"])


if __name__ == "__main__":
    main()
