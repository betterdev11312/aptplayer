"""Radio: fila infinita de musicas parecidas com a faixa semente.

Duas fontes, combinadas:
 1. Mix do YouTube (list=RD<video_id>) - o algoritmo deles e muito bom nisso
    e ja vem com musica relacionada de verdade.
 2. IA local (Ollama) - analisa estilo/clima e sugere artistas parecidos,
    que viram buscas. Entra quando o mix se esgota ou como tempero.

O radio nunca acaba: quando a fila chega perto do fim, a interface pede mais
e a semente passa a ser a ultima faixa tocada.
"""

import random
import re

from yt_dlp import YoutubeDL

from . import ai, youtube

_MIX_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "extract_flat": True,
    "skip_download": True,
}

# Ja usados nesta sessao de radio, para nao repetir faixa.
_seen: set[str] = set()


def reset(seed_id: str | None = None) -> None:
    """Zera a memoria de repeticao (ao iniciar um radio novo)."""
    _seen.clear()
    if seed_id:
        _seen.add(seed_id)


def _mix_tracks(video_id: str, limit: int) -> list[dict]:
    """Faixas do mix que o YouTube gera a partir deste video."""
    url = f"https://www.youtube.com/watch?v={video_id}&list=RD{video_id}"
    opts = {**_MIX_OPTS, "playlistend": limit + 6}
    try:
        with YoutubeDL(opts) as ydl:
            data = ydl.extract_info(url, download=False)
    except Exception:
        return []

    out = []
    for entry in (data or {}).get("entries") or []:
        if not entry:
            continue
        track = youtube._normalize(entry)
        if not track or track["video_id"] in _seen:
            continue
        # O mix ja e curado, mas ainda filtramos o que nao parece musica.
        if youtube.music_score(entry) < -2:
            continue
        _seen.add(track["video_id"])
        out.append(track)
    return out


_SIMILAR_SYSTEM = (
    "Voce recomenda musicas parecidas. Responda SOMENTE com um array JSON de "
    'strings no formato "Artista - Musica". Sem explicacao, sem texto extra. '
    "Escolha musicas reais, conhecidas, de artistas variados - nao repita o "
    "artista da musica de referencia em todas as sugestoes."
)


def _ai_tracks(seed: dict, limit: int) -> list[dict]:
    """Sugestoes da IA a partir do estilo da faixa semente."""
    if not ai.pick_model():
        return []

    context = f"{seed.get('artist', '')} - {seed.get('title', '')}"
    hints = []
    if seed.get("genre"):
        hints.append(f"genero {seed['genre']}")
    if seed.get("mood"):
        hints.append(f"clima {seed['mood']}")
    hint_text = f" ({', '.join(hints)})" if hints else ""

    raw = ai._generate(
        f'Musica de referencia: "{context}"{hint_text}\n\n'
        f"Sugira {limit} musicas de estilo parecido para tocar em sequencia.",
        _SIMILAR_SYSTEM,
    )
    queries = ai._extract_json(raw)
    if not isinstance(queries, list):
        return []

    out = []
    for query in queries[:limit]:
        if not isinstance(query, str):
            continue
        try:
            found = youtube.search(query, limit=1)
        except Exception:
            continue
        for track in found:
            if track["video_id"] not in _seen:
                _seen.add(track["video_id"])
                out.append(track)
    return out


def build(seed: dict, count: int = 12, use_ai: bool = True) -> list[dict]:
    """Monta um lote de faixas para o radio a partir da faixa semente.

    Prioriza o mix do YouTube (rapido e certeiro) e completa com a IA quando
    o mix nao rende o suficiente.
    """
    video_id = seed.get("video_id")
    if not video_id:
        return []

    tracks = _mix_tracks(video_id, count)

    # Mix curto (video obscuro, sem mix): a IA preenche o resto.
    if use_ai and len(tracks) < count:
        tracks += _ai_tracks(seed, count - len(tracks))

    random.shuffle(tracks)
    return tracks[:count]
