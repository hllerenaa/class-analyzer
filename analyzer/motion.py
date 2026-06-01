"""Deteccion de 'playback de video' por movimiento entre frames.

Muestrea 1 fps en gris reducido, calcula diff medio frame-a-frame.
Video reproducido = cambio sostenido alto. Slide estatica / hablar = bajo.
"""
import os
import glob
import tempfile
import subprocess
import numpy as np
from PIL import Image


def motion_per_second(ffmpeg, video_path, sample_w=160, sample_h=90):
    """Retorna lista de floats (diff medio por segundo, 0..255)."""
    tmp = tempfile.mkdtemp(prefix="ca_frames_")
    try:
        out_pat = os.path.join(tmp, "f_%06d.png")
        cmd = [
            ffmpeg, "-hide_banner", "-loglevel", "error",
            "-i", video_path,
            "-vf", f"fps=1,scale={sample_w}:{sample_h},format=gray",
            "-f", "image2", out_pat,
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)

        files = sorted(glob.glob(os.path.join(tmp, "f_*.png")))
        diffs = []
        prev = None
        for fp in files:
            arr = np.asarray(Image.open(fp).convert("L"), dtype=np.int16)
            if prev is not None:
                diffs.append(float(np.mean(np.abs(arr - prev))))
            else:
                diffs.append(0.0)
            prev = arr
        return diffs
    finally:
        for fp in glob.glob(os.path.join(tmp, "*.png")):
            try:
                os.remove(fp)
            except OSError:
                pass
        try:
            os.rmdir(tmp)
        except OSError:
            pass


def playback_per_second(diffs, threshold):
    """True por segundo donde el movimiento supera el umbral (video corriendo)."""
    return [d >= threshold for d in diffs]
