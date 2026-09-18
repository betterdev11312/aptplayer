"""Compartilhar playlists entre usuarios do AptPlayer.

Uma playlist vira um codigo de texto que a outra pessoa cola no app dela.
O codigo carrega os ids do YouTube, entao a playlist e reconstruida identica
- sem servidor no meio, sem conta, sem upload.

Formato: APT1: seguido de JSON compactado em base64 url-safe.
"""

import base64
import json
import re
import zlib

from . import library

PREFIX = "APT1:"
MAX_TRACKS = 500

_CODE = re.compile(r"APT1:([A-Za-z0-9_\-=]+)")


def export_playlist(playlist_id: int) -> dict:
    """Gera o codigo compartilhavel de uma playlist."""
    playlist = library.get_playlist(int(playlist_id))
    if not playlist:
        return {"ok": False, "error": "Playlist nao encontrada."}

    tracks = library.playlist_tracks(int(playlist_id))[:MAX_TRACKS]
    if not tracks:
        return {"ok": False, "error": "Playlist vazia."}

    payload = {
        "n": playlist["name"],
        # so o essencial: o resto o app de destino busca sozinho
        "t": [[t["video_id"], t["title"], t["artist"]] for t in tracks],
    }

    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    packed = zlib.compress(raw.encode("utf-8"), 9)
    code = PREFIX + base64.urlsafe_b64encode(packed).decode("ascii")

    return {
        "ok": True,
        "code": code,
        "name": playlist["name"],
        "count": len(tracks),
        "size": len(code),
    }


def parse_code(code: str) -> dict:
    """Le um codigo e devolve o que tem dentro, sem importar ainda."""
    match = _CODE.search((code or "").strip())
    if not match:
        return {"ok": False, "error": "Codigo invalido. Ele comeca com APT1:"}

    try:
        packed = base64.urlsafe_b64decode(match.group(1))
        raw = zlib.decompress(packed).decode("utf-8")
        data = json.loads(raw)
    except (ValueError, zlib.error, UnicodeDecodeError):
        return {"ok": False, "error": "Codigo corrompido ou incompleto."}

    tracks = data.get("t")
    if not isinstance(tracks, list) or not tracks:
        return {"ok": False, "error": "O codigo nao tem faixas."}

    items = []
    for entry in tracks[:MAX_TRACKS]:
        if isinstance(entry, list) and len(entry) >= 3 and entry[0]:
            items.append({
                "video_id": str(entry[0]),
                "title": str(entry[1]),
                "artist": str(entry[2]),
            })

    if not items:
        return {"ok": False, "error": "Nenhuma faixa valida no codigo."}

    return {
        "ok": True,
        "name": str(data.get("n") or "Playlist compartilhada"),
        "items": items,
        "count": len(items),
    }


def import_code(code: str, name: str = "") -> dict:
    """Cria a playlist a partir do codigo."""
    parsed = parse_code(code)
    if not parsed["ok"]:
        return parsed

    playlist_name = (name or "").strip() or parsed["name"]
    playlist_id = library.create_playlist(playlist_name)

    for item in parsed["items"]:
        library.add_track({
            "video_id": item["video_id"],
            "title": item["title"],
            "artist": item["artist"],
            "duration": 0,
            # a miniatura e derivada do id, entao nao precisa viajar no codigo
            "thumbnail": f"https://i.ytimg.com/vi/{item['video_id']}/mqdefault.jpg",
        })
        library.add_to_playlist(playlist_id, item["video_id"])

    return {
        "ok": True,
        "id": playlist_id,
        "name": playlist_name,
        "count": len(parsed["items"]),
    }
