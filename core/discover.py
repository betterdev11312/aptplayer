"""Tela inicial de descoberta: secoes prontas para navegar sem digitar nada.

As secoes misturam o que o usuario ja ouve (biblioteca, historico) com
descoberta nova (buscas por genero/decada no YouTube). Tudo com cache em
memoria, porque cada secao custa uma busca na rede.
"""

import random
import re
import time
from concurrent.futures import ThreadPoolExecutor

from . import library, youtube

# Secoes de descoberta: (id, titulo, consulta de busca)
# As consultas citam ARTISTAS, nao "as melhores de X" - senao o YouTube
# devolve coletaneas de 2 horas em vez de faixas individuais.
_GENRES = [
    ("rock", "Rock", "Queen Led Zeppelin Nirvana song"),
    ("pop", "Pop", "Dua Lipa The Weeknd Taylor Swift song"),
    ("mpb", "MPB", "Caetano Veloso Djavan Marisa Monte musica"),
    ("rap", "Rap & Hip-Hop", "Racionais Emicida Djonga musica"),
    ("eletronica", "Eletrônica", "Daft Punk Avicii Calvin Harris song"),
    ("metal", "Metal", "Metallica Slipknot Iron Maiden song"),
    ("jazz", "Jazz", "Miles Davis John Coltrane Bill Evans song"),
    ("indie", "Indie", "Arctic Monkeys Tame Impala The Strokes song"),
    ("funk", "Funk", "Anitta Ludmilla MC Hariel musica"),
    ("sertanejo", "Sertanejo", "Jorge Mateus Henrique Juliano musica"),
    ("synthwave", "Synthwave", "Perturbator Carpenter Brut Gunship song"),
    ("lofi", "Lo-fi", "Nujabes Idealism lofi song"),
]

_MOODS = [
    ("foco", "Para focar", "Ludovico Einaudi Nils Frahm piano song"),
    ("treino", "Treino", "Eminem Linkin Park Prodigy song"),
    ("relax", "Relaxar", "Bon Iver Norah Jones Cigarettes After Sex song"),
    ("festa", "Festa", "Bruno Mars Beyonce Black Eyed Peas song"),
    ("viagem", "Viagem", "Fleetwood Mac Eagles Tom Petty song"),
    ("madrugada", "Madrugada", "Radiohead The xx Lana Del Rey song"),
]

_DECADES = [
    ("80s", "Anos 80", "Michael Jackson A-ha Toto song 1980s"),
    ("90s", "Anos 90", "Nirvana Oasis Backstreet Boys song 1990s"),
    ("2000s", "Anos 2000", "Coldplay Linkin Park Beyonce song 2000s"),
    ("2010s", "Anos 2010", "Adele Drake Imagine Dragons song 2010s"),
]

# Cache: secao -> (timestamp, faixas). Descoberta nao precisa ser tempo real.
_CACHE: dict[str, tuple[float, list[dict]]] = {}
_TTL = 6 * 3600


# Coletanea/playlist gravada como video unico: titulo denuncia.
_COLLECTION = re.compile(
    r"(playlist|as melhores|melhores m[uú]sicas|top \d+|mix|sele[cç][aã]o|"
    r"cole[tç][aã]o|greatest hits|nonstop|\d+ ?h(oras?)?|set)",
    re.I,
)


def _is_single_track(track: dict) -> bool:
    """Faixa individual, nao uma coletanea de 2 horas."""
    duration = track.get("duration") or 0
    if duration and duration > 720:          # > 12 min
        return False
    if _COLLECTION.search(track.get("title", "")):
        return False
    if _COLLECTION.search(track.get("artist", "")):
        return False
    return True


def _cached_search(key: str, query: str, limit: int) -> list[dict]:
    hit = _CACHE.get(key)
    if hit and time.time() - hit[0] < _TTL:
        return hit[1]
    try:
        tracks = [t for t in youtube.search(query, limit=limit + 8)
                  if _is_single_track(t)][:limit]
    except Exception:
        return hit[1] if hit else []
    if tracks:
        _CACHE[key] = (time.time(), tracks)
    return tracks


def categories() -> dict:
    """Os chips de categoria que a home mostra (sem custo de rede)."""
    return {
        "genres": [{"id": i, "label": l} for i, l, _ in _GENRES],
        "moods": [{"id": i, "label": l} for i, l, _ in _MOODS],
        "decades": [{"id": i, "label": l} for i, l, _ in _DECADES],
    }


def category_tracks(category_id: str, limit: int = 18) -> list[dict]:
    """Faixas de uma categoria (genero, clima ou decada)."""
    for group in (_GENRES, _MOODS, _DECADES):
        for cid, _label, query in group:
            if cid == category_id:
                return _cached_search(f"cat:{cid}", query, limit)
    return []


def _personal_sections(limit: int) -> list[dict]:
    """Secoes montadas a partir do que o usuario ja tem."""
    sections = []

    recent = library.history(limit)
    if recent:
        sections.append({
            "id": "continue",
            "title": "Continuar ouvindo",
            "subtitle": "de onde você parou",
            "tracks": recent,
        })

    top = library.top_played(limit)
    if len(top) >= 3:
        sections.append({
            "id": "top",
            "title": "Suas mais tocadas",
            "subtitle": "o que você não cansa de repetir",
            "tracks": top,
        })

    favs = library.favorites()[:limit]
    if favs:
        sections.append({
            "id": "favorites",
            "title": "Favoritas",
            "subtitle": "as que você marcou",
            "tracks": favs,
        })

    return sections


def _suggestion_from_library(limit: int) -> dict | None:
    """'Porque voce ouviu X': mix do YouTube a partir de uma faixa recente."""
    from . import radio

    recent = library.history(8)
    if not recent:
        return None

    seed = random.choice(recent[:5])
    radio.reset(seed["video_id"])
    try:
        tracks = radio.build(seed, limit, use_ai=False)
    except Exception:
        return None
    if not tracks:
        return None

    return {
        "id": "because",
        "title": f"Porque você ouviu {seed['artist']}",
        "subtitle": seed["title"],
        "tracks": tracks,
    }


def home(limit: int = 18) -> list[dict]:
    """Monta a home: pessoal primeiro, depois descoberta.

    As secoes de descoberta sao buscadas em paralelo - em serie a home
    levaria mais de 20s.
    """
    sections = _personal_sections(limit)

    picks = random.sample(_GENRES, 3) + random.sample(_MOODS, 2)

    with ThreadPoolExecutor(max_workers=6) as pool:
        because_future = pool.submit(_suggestion_from_library, limit)
        futures = [
            (cid, label, pool.submit(_cached_search, f"cat:{cid}", query, limit))
            for cid, label, query in picks
        ]

        because = because_future.result()
        if because:
            sections.insert(1 if sections else 0, because)

        for cid, label, future in futures:
            tracks = future.result()
            if tracks:
                sections.append({
                    "id": f"cat-{cid}",
                    "title": label,
                    "subtitle": "descobrir",
                    "tracks": tracks,
                })

    return sections
