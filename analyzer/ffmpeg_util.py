"""Localiza binarios ffmpeg/ffprobe (PATH o instalacion winget)."""
import os
import glob
import shutil


def _winget_candidates(exe):
    local = os.environ.get("LOCALAPPDATA", "")
    if not local:
        return []
    pat = os.path.join(
        local, "Microsoft", "WinGet", "Packages",
        "Gyan.FFmpeg*", "*", "bin", exe
    )
    return glob.glob(pat)


def find_binary(name, ffmpeg_dir=""):
    """Devuelve ruta absoluta a ffmpeg/ffprobe o None."""
    exe = name + (".exe" if os.name == "nt" else "")
    # 1) dir explicito
    if ffmpeg_dir:
        cand = os.path.join(ffmpeg_dir, exe)
        if os.path.isfile(cand):
            return cand
    # 2) PATH
    found = shutil.which(name)
    if found:
        return found
    # 3) winget
    cands = _winget_candidates(exe)
    if cands:
        return cands[0]
    return None


def resolve(ffmpeg_dir=""):
    ffmpeg = find_binary("ffmpeg", ffmpeg_dir)
    ffprobe = find_binary("ffprobe", ffmpeg_dir)
    if not ffmpeg or not ffprobe:
        raise RuntimeError(
            "No se encontro ffmpeg/ffprobe. Instala con "
            "'winget install Gyan.FFmpeg' o define ffmpeg_dir."
        )
    return ffmpeg, ffprobe
