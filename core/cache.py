"""Cache hibrido: streama sempre, baixa em background o que voce mais ouve."""

import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from yt_dlp import YoutubeDL

from . import library, youtube
from .paths import CACHE_DIR

# A partir de quantas reproducoes uma faixa vira arquivo local.
CACHE_THRESHOLD = 3

_pool = ThreadPoolExecutor(max_workers=2)
_in_flight: set[str] = set()
_failed: set[str] = set()
_lock = threading.Lock()


def _download_opts(target: Path, client: str) -> dict:
    return {
        "quiet": True,
        "no_warnings": True,
        "format": "bestaudio/best",
        "outtmpl": str(target.with_suffix(".%(ext)s")),
        "extractor_args": {"youtube": {"player_client": [client]}},
    }


def cached_file(video_id: str) -> str | None:
    """Caminho local da faixa, se ja estiver baixada e o arquivo existir."""
    track = library.get_track(video_id)
    if not track or not track.get("cached_path"):
        return None
    path = Path(track["cached_path"])
    if path.exists():
        return str(path)
    # Arquivo sumiu do disco: limpa o registro.
    library.set_cached_path(video_id, None)
    return None


def _do_download(video_id: str) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        target = CACHE_DIR / video_id
        for client in youtube.PLAYER_CLIENTS:
            try:
                with YoutubeDL(_download_opts(target, client)) as ydl:
                    info = ydl.extract_info(
                        f"https://www.youtube.com/watch?v={video_id}", download=True
                    )
            except Exception:
                continue  # cliente bloqueado; tenta o proximo
            final = target.with_suffix(f".{info.get('ext', 'm4a')}")
            if final.exists():
                library.set_cached_path(video_id, str(final))
                with _lock:
                    _failed.discard(video_id)
                return
        # Nenhum cliente do YouTube entregou o audio.
        with _lock:
            _failed.add(video_id)
    finally:
        with _lock:
            _in_flight.discard(video_id)


def maybe_cache(video_id: str) -> None:
    """Agenda o download se a faixa ja passou do limite de reproducoes."""
    track = library.get_track(video_id)
    if not track:
        return
    if track.get("cached_path") and Path(track["cached_path"]).exists():
        return
    if track.get("play_count", 0) < CACHE_THRESHOLD:
        return

    with _lock:
        if video_id in _in_flight:
            return
        _in_flight.add(video_id)
    _pool.submit(_do_download, video_id)


def force_cache(video_id: str) -> str:
    """Baixa agora, independente do contador (acao manual do usuario).

    Devolve: "ready" (ja estava), "downloading" (ja estava na fila) ou
    "queued" (acabou de entrar na fila).
    """
    if cached_file(video_id):
        return "ready"
    with _lock:
        if video_id in _in_flight:
            return "downloading"
        _in_flight.add(video_id)
        _failed.discard(video_id)
    _pool.submit(_do_download, video_id)
    return "queued"


def status(video_id: str) -> str:
    """Estado do cache desta faixa: ready | downloading | failed | none."""
    if cached_file(video_id):
        return "ready"
    with _lock:
        if video_id in _in_flight:
            return "downloading"
        if video_id in _failed:
            return "failed"
    return "none"


def status_many(video_ids: list[str]) -> dict[str, str]:
    """Estado de varias faixas de uma vez (a interface pede em lote)."""
    return {vid: status(vid) for vid in video_ids}


def cache_many(video_ids: list[str]) -> dict:
    """Coloca varias faixas na fila de download (playlist inteira)."""
    queued = ready = 0
    for video_id in video_ids:
        result = force_cache(video_id)
        if result == "ready":
            ready += 1
        elif result == "queued":
            queued += 1
    return {"queued": queued, "already": ready, "total": len(video_ids)}


def remove_cached(video_id: str) -> None:
    path = cached_file(video_id)
    if path:
        try:
            Path(path).unlink()
        except OSError:
            pass
    library.set_cached_path(video_id, None)


def cache_stats() -> dict:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    files = [f for f in CACHE_DIR.iterdir() if f.is_file()]
    total = sum(f.stat().st_size for f in files)
    with _lock:
        downloading = len(_in_flight)
        failed = len(_failed)
    return {
        "files": len(files),
        "size_mb": round(total / (1024 * 1024), 1),
        "downloading": downloading,
        "failed": failed,
    }
