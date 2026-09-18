"""Importa playlists e albuns publicos do Spotify - sem API key, sem login.

O player embutido (open.spotify.com/embed/...) entrega a lista de faixas no
HTML inicial, dentro do JSON __NEXT_DATA__. E o mesmo dado que qualquer site
com um player do Spotify recebe.

O Spotify nao da o audio: cada faixa e procurada no YouTube pelo nome. Por
isso a importacao demora alguns segundos por musica.
"""

import json
import re

import requests

from . import youtube

TIMEOUT = 20
_UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

_NEXT_DATA = re.compile(
    r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S
)

# Aceita link normal, com parametros, ou URI (spotify:playlist:xxx)
_LINK = re.compile(
    r"(?:open\.spotify\.com/(?:intl-\w+/)?|spotify:)"
    r"(playlist|album|track)[/:]([A-Za-z0-9]+)",
    re.I,
)


def parse_link(url: str) -> tuple[str, str] | None:
    """Extrai (tipo, id) de um link do Spotify. None se nao reconhecer."""
    match = _LINK.search(url or "")
    if not match:
        return None
    return match.group(1).lower(), match.group(2)


def _find_tracklist(node, depth: int = 0):
    """Procura a chave trackList em qualquer nivel do JSON."""
    if depth > 10:
        return None
    if isinstance(node, dict):
        if isinstance(node.get("trackList"), list):
            return node["trackList"]
        for value in node.values():
            found = _find_tracklist(value, depth + 1)
            if found:
                return found
    elif isinstance(node, list):
        for value in node:
            found = _find_tracklist(value, depth + 1)
            if found:
                return found
    return None


def fetch_tracks(url: str) -> dict:
    """Le a playlist/album/faixa. Devolve {name, items:[{artist,title}]}."""
    parsed = parse_link(url)
    if not parsed:
        return {"ok": False, "error": "Link do Spotify invalido."}

    kind, spotify_id = parsed
    embed = f"https://open.spotify.com/embed/{kind}/{spotify_id}"

    try:
        response = requests.get(embed, timeout=TIMEOUT, headers=_UA)
        response.raise_for_status()
    except requests.RequestException as exc:
        return {"ok": False, "error": f"Nao consegui abrir o link: {exc}"}

    match = _NEXT_DATA.search(response.text)
    if not match:
        return {
            "ok": False,
            "error": "O Spotify mudou o formato da pagina. Playlist e publica?",
        }

    try:
        data = json.loads(match.group(1))
    except ValueError:
        return {"ok": False, "error": "Resposta do Spotify ilegivel."}

    track_list = _find_tracklist(data)
    if not track_list:
        return {
            "ok": False,
            "error": "Nenhuma faixa encontrada. A playlist precisa ser publica.",
        }

    # nome da playlist, quando disponivel
    name = ""
    def find_name(node, depth=0):
        nonlocal name
        if name or depth > 8:
            return
        if isinstance(node, dict):
            if node.get("type") in ("playlist", "album") and node.get("name"):
                name = node["name"]
                return
            for value in node.values():
                find_name(value, depth + 1)
        elif isinstance(node, list):
            for value in node:
                find_name(value, depth + 1)
    find_name(data)

    items = []
    for entry in track_list:
        title = (entry.get("title") or "").strip()
        artist = (entry.get("subtitle") or "").strip()
        if title:
            items.append({"artist": artist, "title": title})

    if not items:
        return {"ok": False, "error": "A lista veio vazia."}

    return {
        "ok": True,
        "kind": kind,
        "name": name or f"Importada do Spotify",
        "items": items,
    }


def match_on_youtube(items: list[dict], limit: int = 0,
                     progress=None) -> list[dict]:
    """Procura cada faixa no YouTube. progress(feito, total, faixa)."""
    if limit:
        items = items[:limit]

    found = []
    total = len(items)
    for index, item in enumerate(items, 1):
        query = f"{item['artist']} {item['title']}".strip()
        try:
            results = youtube.search(query, limit=1)
        except Exception:
            results = []
        if results:
            found.append(results[0])
        if progress:
            progress(index, total, query)
    return found
