"""Busca e resolucao de streams do YouTube via yt-dlp.

A busca prioriza musica de verdade em duas camadas:
 1. YouTube Music (music.youtube.com) so indexa musica, entao os ids que ele
    devolve sao confiaveis - mas ele nao traz duracao nem artista.
 2. A busca normal traz os metadados, e uma heuristica derruba o que tem cara
    de vlog/gameplay/podcast quando o YT Music nao cobre a consulta.
"""

import re
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

from yt_dlp import YoutubeDL

# URLs de stream do YouTube expiram (~6h). Guardamos com folga menor.
_STREAM_TTL = 3 * 3600

_FLAT_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "extract_flat": True,
    "skip_download": True,
    "default_search": "ytsearch",
}

# O YouTube barra alguns clientes com verificacao anti-bot, e quais funcionam
# muda com o tempo. Tentamos em ordem ate um resolver.
PLAYER_CLIENTS = ["android", "tv", "web_embedded", "mweb", "web"]

# Ids de video tem 11 chars; canais (UC...) e albuns (MPREb...) nao servem.
_VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")

# Marcadores de conteudo que nao e musica.
_NOT_MUSIC = re.compile(
    r"\b(vlog|reagindo|rea[cç][aã]o|react|gameplay|tutorial|unboxing|podcast|"
    r"entrevista|epis[oó]dio|minecraft|roblox|free ?fire|pegadinha|desafio|"
    r"challenge|paranormal|story ?time|meu dia|rotina|corte[s]? do|"
    r"como (eu |ele |ela )?(dei|fiz|faz|ganhei)|document[aá]rio|an[aá]lise|"
    r"explicando|resumo|trailer|review|walkthrough|no commentary|speedrun|"
    r"survival|hardcore|longplay|full game|lyrics? analysis|compilation|"
    r"best of \d+|top \d+|\d+ ?(dias?|days?) (no|in|de)|asmr|como fazer)\b",
    re.I,
)

_MUSIC_HINT = re.compile(
    r"\b(official|oficial|lyric|letra|audio|clipe|ao vivo|live|remaster|"
    r"acoustic|ac[uú]stico|cover|feat|ft|remix|album|full song)\b",
    re.I,
)

_SHOUTY = re.compile(r"[A-ZÀ-Ý]{4,}")

_NOISE_TOKENS = [
    "(Official Video)", "(Official Music Video)", "(Official Audio)",
    "[Official Video]", "[Official Music Video]", "[Official Audio]",
    "(Lyric Video)", "(Lyrics)", "(Visualizer)", "(Audio)",
    "(Official Lyric Video)", "(HD)", "(HQ)", "(4K)", "(Clipe Oficial)",
    "(Videoclipe Oficial)", "(Video Oficial)", "(Audio Oficial)",
]

_stream_cache: dict[str, tuple[float, str]] = {}
_pool = ThreadPoolExecutor(max_workers=4)


def _duration_label(seconds) -> str:
    if not seconds:
        return ""
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _thumb_for(video_id: str) -> str:
    return f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg"


def _clean_title(title: str) -> str:
    """Remove o lixo tipico de titulo de YouTube."""
    out = title
    for token in _NOISE_TOKENS:
        out = re.sub(re.escape(token), "", out, flags=re.I)
    return " ".join(out.split()).strip(" -–—|")


_QUALITY = re.compile(
    r"\s*[\[(]\s*(4k|8k|hd|hq|full ?hd|1080p?|720p?|"
    r"(4k|hd|hq)?\s*upgrade|remaster(ed)?( \d{4})?|"
    r"official (hd )?(music )?video|official video|hd video)\s*[\])]",
    re.I,
)


def _strip_quality(title: str) -> str:
    """Tira sufixos tipo [4K UPGRADE] / (Official HD Music Video)."""
    return " ".join(_QUALITY.sub(" ", title).split()).strip(" -–—|")


def _split_artist_title(title: str, uploader: str = "") -> tuple[str, str]:
    """Separa 'Artista - Musica'.

    Alguns canais publicam invertido ('Musica - Artista'); quando um dos lados
    bate com o nome do canal, ele e o artista.
    """
    for sep in (" - ", " – ", " — "):
        if sep not in title:
            continue
        left, _, right = title.partition(sep)
        left, right = left.strip(), right.strip()
        if not left or not right:
            continue

        channel = (uploader or "").replace(" - Topic", "").strip().casefold()
        if channel:
            if right.casefold() == channel:
                return right, left          # veio invertido
            if left.casefold() == channel:
                return left, right
        return left, right
    return "", title


def music_score(entry: dict) -> float:
    """Quanto esta entrada parece musica. Negativo = provavelmente nao e."""
    title = entry.get("title") or ""
    duration = entry.get("duration") or 0
    uploader = entry.get("uploader") or entry.get("channel") or ""

    score = 0.0

    # Duracao: musica quase sempre cai entre ~1min e ~15min.
    if 75 <= duration <= 900:
        score += 2
    elif duration and (duration < 45 or duration > 1800):
        score -= 3

    # Canais "- Topic" sao gerados pelo YouTube Music: sempre musica.
    if uploader.endswith("- Topic"):
        score += 4

    if _MUSIC_HINT.search(title):
        score += 1.5
    if re.search(r"(official|oficial).{0,3}(video|audio|music)", title, re.I):
        score += 1.5
    if " - " in title or " – " in title:
        score += 1.5

    if _NOT_MUSIC.search(title):
        score -= 6
    # TITULO TODO GRITADO costuma ser vlog/clickbait.
    if len(_SHOUTY.findall(title)) >= 3:
        score -= 2

    return score


def _normalize(entry: dict) -> dict | None:
    if not entry or not entry.get("id") or not _VIDEO_ID.match(entry["id"]):
        return None
    raw_title = entry.get("title") or ""
    clean = _strip_quality(_clean_title(raw_title))
    if not clean:
        return None
    uploader = (entry.get("uploader") or entry.get("channel") or "")
    uploader = uploader.replace(" - Topic", "").strip()
    parsed_artist, parsed_title = _split_artist_title(clean, uploader)
    duration = entry.get("duration") or 0

    return {
        "video_id": entry["id"],
        "title": parsed_title or clean,
        "artist": parsed_artist or uploader or "Desconhecido",
        "duration": duration,
        "duration_label": _duration_label(duration),
        "thumbnail": _thumb_for(entry["id"]),
    }


def _flat_search(url: str, limit: int) -> list[dict]:
    opts = {**_FLAT_OPTS, "playlistend": limit}
    try:
        with YoutubeDL(opts) as ydl:
            data = ydl.extract_info(url, download=False)
    except Exception:
        return []
    return [e for e in (data or {}).get("entries") or [] if e]


def _music_ids(query: str, limit: int) -> list[str]:
    """Ids vindos do YouTube Music - fonte confiavel de 'isto e musica'."""
    url = f"https://music.youtube.com/search?q={urllib.parse.quote(query)}"
    return [
        e["id"] for e in _flat_search(url, limit)
        if e.get("id") and _VIDEO_ID.match(e["id"])
    ]


def search(query: str, limit: int = 20, music_only: bool = True) -> list[dict]:
    """Busca musica no YouTube.

    Com music_only, o que o YouTube Music reconhece vem primeiro e o resto e
    filtrado pela heuristica. Sem ele, e uma busca crua.
    """
    query = (query or "").strip()
    if not query:
        return []

    entries = _flat_search(f"ytsearch{limit}:{query}", limit)
    if not music_only:
        return [t for t in map(_normalize, entries) if t][:limit]

    # Ids que o YouTube Music confirma como musica.
    try:
        confirmed = set(_music_ids(query, limit))
    except Exception:
        confirmed = set()

    scored = []
    for entry in entries:
        track = _normalize(entry)
        if not track:
            continue
        score = music_score(entry)
        if track["video_id"] in confirmed:
            score += 5  # o YT Music ja garantiu que e musica
        scored.append((score, track))

    # Mantem o que tem cara de musica; se a heuristica zerar tudo, devolve o
    # melhor que houver para nao deixar o usuario sem resultado.
    ranked = sorted(scored, key=lambda x: -x[0])
    keep = [t for s, t in ranked if s >= 1]
    if not keep:
        # Nada passou o corte: aceita o que nao for claramente outra coisa,
        # para o usuario ver algo em vez de uma tela vazia.
        keep = [t for s, t in ranked if s > -3]
    return keep[:limit]


def get_stream_url(video_id: str) -> str | None:
    """Resolve a URL direta de audio, usando cache enquanto nao expira."""
    cached = _stream_cache.get(video_id)
    if cached and time.time() - cached[0] < _STREAM_TTL:
        return cached[1]

    for client in PLAYER_CLIENTS:
        try:
            with YoutubeDL(_stream_opts(client)) as ydl:
                info = ydl.extract_info(
                    f"https://www.youtube.com/watch?v={video_id}", download=False
                )
        except Exception:
            continue  # cliente bloqueado ou sem formato; tenta o proximo

        url = info.get("url")
        if not url:
            # Alguns clientes so expoem a URL dentro da lista de formatos.
            for fmt in reversed(info.get("formats") or []):
                if fmt.get("acodec") not in (None, "none") and fmt.get("url"):
                    url = fmt["url"]
                    break

        if url:
            _stream_cache[video_id] = (time.time(), url)
            return url

    return None


def _stream_opts(client: str) -> dict:
    return {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "format": "bestaudio/best",
        "extractor_args": {"youtube": {"player_client": [client]}},
    }


def prefetch_stream(video_id: str) -> None:
    """Resolve a proxima faixa em background para a troca ser instantanea."""
    cached = _stream_cache.get(video_id)
    if cached and time.time() - cached[0] < _STREAM_TTL:
        return
    _pool.submit(get_stream_url, video_id)
