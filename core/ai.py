"""Integracao com Ollama local: busca em linguagem natural, playlists e auto-tag."""

import json
import re

import requests

from . import library

OLLAMA_URL = "http://localhost:11434"
TIMEOUT = 60

# Ordem de preferencia quando o usuario nao escolheu modelo.
_PREFERRED = ["llama3.2", "llama3.1", "llama3", "qwen2.5", "mistral", "gemma2", "phi3"]

_model_cache: str | None = None


def is_available() -> bool:
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        return r.status_code == 200
    except requests.RequestException:
        return False


def list_models() -> list[str]:
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        r.raise_for_status()
        return [m["name"] for m in r.json().get("models", [])]
    except requests.RequestException:
        return []


def pick_model() -> str | None:
    """Escolhe o melhor modelo disponivel, preferindo os conhecidos."""
    global _model_cache
    if _model_cache and _model_cache in list_models():
        return _model_cache

    models = list_models()
    if not models:
        _model_cache = None
        return None

    for preferred in _PREFERRED:
        for model in models:
            if model.startswith(preferred):
                _model_cache = model
                return model

    _model_cache = models[0]
    return _model_cache


def set_model(name: str) -> None:
    global _model_cache
    _model_cache = name


def _generate(prompt: str, system: str = "") -> str | None:
    model = pick_model()
    if not model:
        return None
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "system": system,
                "stream": False,
                "options": {"temperature": 0.7},
            },
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        return r.json().get("response", "")
    except requests.RequestException:
        return None


def _extract_json(text: str):
    """Modelos locais gostam de embrulhar JSON em texto; desembrulha."""
    if not text:
        return None
    fenced = re.search(r"```(?:json)?\s*(.+?)```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    match = re.search(r"[\[{].*[\]}]", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


# --- 1. busca em linguagem natural ---------------------------------------

_SEARCH_SYSTEM = (
    "Voce traduz pedidos de musica em consultas de busca para o YouTube. "
    "Responda SOMENTE com um array JSON de 5 strings, cada uma no formato "
    '"Artista - Musica". Sem explicacao, sem texto extra.'
)


def queries_from_request(request: str) -> list[str]:
    """'algo tipo Pink Floyd mas mais pesado' -> lista de buscas concretas."""
    raw = _generate(
        f'Pedido do usuario: "{request}"\n\n'
        "Sugira 5 musicas reais e conhecidas que atendam a esse pedido.",
        _SEARCH_SYSTEM,
    )
    data = _extract_json(raw)
    if isinstance(data, list):
        return [str(q) for q in data if isinstance(q, (str, int))][:5]
    return []


# --- 2. gerar playlist a partir da biblioteca ----------------------------

_PLAYLIST_SYSTEM = (
    "Voce monta playlists a partir de uma biblioteca existente. "
    "Responda SOMENTE com um array JSON de numeros: os indices das faixas escolhidas, "
    "na melhor ordem de reproducao. Sem texto extra."
)


def playlist_from_library(description: str, max_tracks: int = 15) -> list[str]:
    """Escolhe faixas da biblioteca que combinam com a descricao dada."""
    tracks = library.all_tracks()
    if not tracks:
        return []

    listing = "\n".join(
        f"{i}. {t['artist']} - {t['title']}"
        + (f" [{t['genre']}]" if t.get("genre") else "")
        for i, t in enumerate(tracks[:150])
    )

    raw = _generate(
        f"Biblioteca:\n{listing}\n\n"
        f'Monte uma playlist de ate {max_tracks} faixas para: "{description}"',
        _PLAYLIST_SYSTEM,
    )
    data = _extract_json(raw)
    if not isinstance(data, list):
        return []

    picked = []
    for idx in data[:max_tracks]:
        if isinstance(idx, int) and 0 <= idx < len(tracks):
            picked.append(tracks[idx]["video_id"])
    return picked


# --- 3. organizar biblioteca (auto-tag) ----------------------------------

_TAG_SYSTEM = (
    "Voce classifica musicas. Responda SOMENTE com um array JSON de objetos "
    '{"i": indice, "genre": "genero", "mood": "clima"}. '
    "Genero em uma palavra (rock, pop, jazz, eletronica, mpb, rap, classica...). "
    "Clima em uma palavra (energetico, calmo, melancolico, feliz, intenso, focado...). "
    "Sem texto extra."
)


def tag_tracks(limit: int = 20) -> int:
    """Classifica faixas sem genero. Devolve quantas foram atualizadas."""
    tracks = library.untagged_tracks(limit)
    if not tracks:
        return 0

    listing = "\n".join(
        f"{i}. {t['artist']} - {t['title']}" for i, t in enumerate(tracks)
    )
    raw = _generate(f"Classifique estas musicas:\n{listing}", _TAG_SYSTEM)
    data = _extract_json(raw)
    if not isinstance(data, list):
        return 0

    updated = 0
    for item in data:
        if not isinstance(item, dict):
            continue
        idx = item.get("i")
        if not isinstance(idx, int) or not 0 <= idx < len(tracks):
            continue
        genre = str(item.get("genre", "")).strip().lower() or None
        mood = str(item.get("mood", "")).strip().lower() or None
        if genre or mood:
            library.set_tags(tracks[idx]["video_id"], genre, mood)
            updated += 1
    return updated


# --- 4. chat livre com a IA ----------------------------------------------

_CHAT_SYSTEM = (
    "Voce e o assistente do AptPlayer, um player de musica. "
    "Fale em portugues do Brasil, de forma direta e amigavel. "
    "Voce entende muito de musica: artistas, generos, historia, recomendacoes. "
    "Quando sugerir musicas para o usuario ouvir, liste cada uma em uma linha "
    'no formato exato: PLAY: Artista - Musica. '
    "Fora isso, converse normalmente. Seja conciso."
)

PLAY_LINE = re.compile(r"^\s*PLAY:\s*(.+)$", re.M | re.I)


def chat(messages: list[dict], library_context: bool = True) -> str | None:
    """Conversa com historico. messages = [{role, content}, ...]."""
    model = pick_model()
    if not model:
        return None

    system = _CHAT_SYSTEM
    if library_context:
        tracks = library.all_tracks()[:40]
        if tracks:
            listing = ", ".join(f"{t['artist']} - {t['title']}" for t in tracks)
            system += f"\n\nBiblioteca atual do usuario: {listing}"

    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": model,
                "messages": [{"role": "system", "content": system}] + messages,
                "stream": False,
                "options": {"temperature": 0.8},
            },
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        return r.json().get("message", {}).get("content", "")
    except requests.RequestException:
        return None


def extract_play_requests(text: str) -> list[str]:
    """Pega as linhas 'PLAY: Artista - Musica' da resposta da IA."""
    return [m.strip() for m in PLAY_LINE.findall(text or "") if m.strip()][:8]


def strip_play_lines(text: str) -> str:
    """Remove as linhas PLAY: do texto exibido no chat."""
    return "\n".join(
        line for line in (text or "").splitlines()
        if not PLAY_LINE.match(line)
    ).strip()
