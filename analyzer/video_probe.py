"""Metadatos del video via ffprobe."""
import json
import subprocess


def probe(ffprobe, video_path):
    cmd = [
        ffprobe, "-v", "error",
        "-print_format", "json",
        "-show_format", "-show_streams",
        video_path,
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    data = json.loads(out)

    duration = float(data.get("format", {}).get("duration", 0.0) or 0.0)
    width = height = 0
    fps = 0.0
    for s in data.get("streams", []):
        if s.get("codec_type") == "video":
            width = int(s.get("width", 0) or 0)
            height = int(s.get("height", 0) or 0)
            rate = s.get("avg_frame_rate") or s.get("r_frame_rate") or "0/1"
            try:
                num, den = rate.split("/")
                fps = float(num) / float(den) if float(den) else 0.0
            except Exception:
                fps = 0.0
            break
    return {
        "duration": duration,
        "width": width,
        "height": height,
        "fps": round(fps, 2),
    }
