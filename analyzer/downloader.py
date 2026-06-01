"""Descarga videos desde URL (YouTube, Drive, y ~1000 sitios) via yt-dlp.

SharePoint/Teams protegidos requieren auth (Microsoft Graph) -> fase 2.
Para esos, descarga manual y usa la ruta local.
"""
import os
import tempfile


def is_url(text):
    return isinstance(text, str) and text.strip().lower().startswith(("http://", "https://"))


def looks_protected(url):
    """Heuristica: links que normalmente requieren login."""
    u = url.lower()
    return any(s in u for s in (
        "sharepoint.com", "teams.microsoft.com", "1drv.ms",
        "onedrive.live.com",
    ))


def download(url, dest_dir=None, log=print):
    """Descarga el video a un archivo temporal. Retorna ruta local.

    Lanza RuntimeError con mensaje claro si falla o requiere auth.
    """
    try:
        import yt_dlp
    except Exception as e:
        raise RuntimeError(
            "yt-dlp no instalado. Ejecuta: pip install yt-dlp"
        ) from e

    if looks_protected(url):
        log("Aviso: URL parece protegida (SharePoint/Teams/OneDrive). "
            "Si falla, descarga manual y usa la ruta local.")

    dest_dir = dest_dir or tempfile.mkdtemp(prefix="ca_dl_")
    outtmpl = os.path.join(dest_dir, "%(id)s.%(ext)s")

    opts = {
        "outtmpl": outtmpl,
        "format": "mp4/bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "quiet": True,
        "noprogress": True,
        "noplaylist": True,
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
            # tras merge puede cambiar a .mp4
            if not os.path.isfile(path):
                base = os.path.splitext(path)[0]
                for ext in (".mp4", ".mkv", ".webm"):
                    if os.path.isfile(base + ext):
                        path = base + ext
                        break
    except Exception as e:
        raise RuntimeError(
            f"No se pudo descargar la URL. Causa: {e}. "
            "Si es SharePoint/Teams/Drive privado, necesita autenticacion; "
            "descarga manual y usa la ruta local."
        ) from e

    if not os.path.isfile(path):
        raise RuntimeError("Descarga termino pero no se encontro el archivo.")
    log(f"Descargado: {path}")
    return path


def resolve_source(source, log=print):
    """Si source es URL la descarga; si es ruta local la valida.
    Retorna ruta local de un archivo de video.
    """
    if is_url(source):
        log("Detectada URL. Descargando con yt-dlp...")
        return download(source, log=log)
    if not source or not os.path.isfile(source):
        raise RuntimeError(f"Ruta de video invalida: {source}")
    return source
