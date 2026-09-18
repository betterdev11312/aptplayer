"""Letras de musica via LRCLIB - API publica, sem chave e sem cadastro.

Quando existe letra sincronizada (formato LRC), o player destaca a linha atual.
Sem sincronia, mostra o texto corrido. Nada e obrigatorio: se falhar, a aba
simplesmente diz que nao achou.
"""

import re
import threading

import requests

from .paths import DATA_DIR

API = "https://lrclib.net/api/search"
TIMEOUT = 10

# Cache em memoria por sessao: letra nao muda.
_cache: dict[str, dict | None] = {}
_lock = threading.Lock()

_LRC_LINE = re.compile(r"\[(\d{2}):(\d{2})[.:](\d{2,3})\]\s*(.*)")

# Ruido que atrapalha a busca por letra.
_CLEAN = re.compile(
    r"\s*[\[(](official|oficial|lyric|letra|audio|video|clipe|hd|hq|4k|remaster"
    r"|ao vivo|live|visualizer)[^\])]*[\])]",
    re.I,
)


def _clean_query(text: str) -> str:
    return " ".join(_CLEAN.sub("", text or "").split()).strip(" -–—|")


def parse_lrc(text: str) -> list[dict]:
    """Converte texto LRC em [{time, line}, ...] ordenado."""
    out = []
    for raw in (text or "").splitlines():
        match = _LRC_LINE.match(raw)
        if not match:
            continue
        mm, ss, frac, line = match.groups()
        # centesimos ou milesimos, conforme o arquivo
        divisor = 1000 if len(frac) == 3 else 100
        seconds = int(mm) * 60 + int(ss) + int(frac) / divisor
        out.append({"time": round(seconds, 2), "line": line.strip()})
    out.sort(key=lambda item: item["time"])
    return out


def fetch(artist: str, title: str, duration: int = 0) -> dict | None:
    """Busca a letra. Devolve {synced, lines, plain} ou None."""
    artist = _clean_query(artist)
    title = _clean_query(title)
    if not title:
        return None

    key = f"{artist.casefold()}|{title.casefold()}"
    with _lock:
        if key in _cache:
            return _cache[key]

    params = {"track_name": title}
    if artist and artist.casefold() != "desconhecido":
        params["artist_name"] = artist

    try:
        response = requests.get(
            API, params=params, timeout=TIMEOUT,
            headers={"User-Agent": "AptPlayer (local music player)"},
        )
        response.raise_for_status()
        results = response.json()
    except (requests.RequestException, ValueError):
        return None

    if not isinstance(results, list) or not results:
        with _lock:
            _cache[key] = None
        return None

    # Prefere o resultado com letra sincronizada e duracao parecida.
    def score(item):
        points = 0
        if item.get("syncedLyrics"):
            points += 10
        if duration and item.get("duration"):
            if abs(item["duration"] - duration) <= 5:
                points += 5
            elif abs(item["duration"] - duration) > 30:
                points -= 5
        return points

    best = max(results, key=score)

    synced = best.get("syncedLyrics")
    plain = best.get("plainLyrics")
    if not synced and not plain:
        with _lock:
            _cache[key] = None
        return None

    data = {
        "synced": bool(synced),
        "lines": parse_lrc(synced) if synced else [],
        "plain": plain or "",
        "artist": best.get("artistName", artist),
        "title": best.get("trackName", title),
    }
    with _lock:
        _cache[key] = data
    return data
