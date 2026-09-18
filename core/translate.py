"""Traducao de letras.

Duas fontes, nesta ordem:
 1. MyMemory - API publica, sem cadastro, ~5000 caracteres por dia
 2. Ollama local - sem limite e privado, se estiver rodando

O Google Translate publico foi testado e responde 429 (rate limit) em textos
do tamanho de uma letra, entao nao serve.

As traducoes ficam em cache no disco: letra traduzida nao muda.
"""

import json
import threading
import time

import requests

from .paths import DATA_DIR

MYMEMORY = "https://api.mymemory.translated.net/get"
TIMEOUT = 25
CHUNK = 480          # o MyMemory corta textos longos; mandamos em pedacos

_cache_file = DATA_DIR / "translations.json"
_cache: dict | None = None
_lock = threading.Lock()

_UA = {"User-Agent": "AptPlayer (local music player)"}


# 80+ idiomas, com o nome em portugues para a interface
LANGUAGES = [
    ("af", "Africâner"), ("sq", "Albanês"), ("de", "Alemão"),
    ("am", "Amárico"), ("ar", "Árabe"), ("hy", "Armênio"),
    ("az", "Azerbaijano"), ("bn", "Bengali"), ("be", "Bielorrusso"),
    ("my", "Birmanês"), ("bs", "Bósnio"), ("bg", "Búlgaro"),
    ("ca", "Catalão"), ("kk", "Cazaque"), ("km", "Khmer"),
    ("si", "Cingalês"), ("ko", "Coreano"), ("hr", "Croata"),
    ("da", "Dinamarquês"), ("sk", "Eslovaco"), ("sl", "Esloveno"),
    ("es", "Espanhol"), ("eo", "Esperanto"), ("et", "Estoniano"),
    ("fi", "Finlandês"), ("fr", "Francês"), ("gl", "Galego"),
    ("cy", "Galês"), ("ka", "Georgiano"), ("el", "Grego"),
    ("gu", "Guzerate"), ("ht", "Haitiano"), ("ha", "Hauçá"),
    ("he", "Hebraico"), ("hi", "Híndi"), ("nl", "Holandês"),
    ("hu", "Húngaro"), ("id", "Indonésio"), ("en", "Inglês"),
    ("yo", "Ioruba"), ("ga", "Irlandês"), ("is", "Islandês"),
    ("it", "Italiano"), ("ja", "Japonês"), ("jv", "Javanês"),
    ("kn", "Canarim"), ("ky", "Quirguiz"), ("lo", "Laosiano"),
    ("la", "Latim"), ("lv", "Letão"), ("lt", "Lituano"),
    ("lb", "Luxemburguês"), ("mk", "Macedônio"), ("ms", "Malaio"),
    ("ml", "Malaiala"), ("mt", "Maltês"), ("mi", "Maori"),
    ("mr", "Marati"), ("mn", "Mongol"), ("ne", "Nepalês"),
    ("no", "Norueguês"), ("fa", "Persa"), ("pl", "Polonês"),
    ("pt", "Português"), ("pa", "Punjabi"), ("ro", "Romeno"),
    ("ru", "Russo"), ("sr", "Sérvio"), ("st", "Sesoto"),
    ("sn", "Shona"), ("sd", "Sindi"), ("so", "Somali"),
    ("sw", "Suaíli"), ("sv", "Sueco"), ("su", "Sundanês"),
    ("tg", "Tadjique"), ("th", "Tailandês"), ("ta", "Tâmil"),
    ("cs", "Tcheco"), ("te", "Telugo"), ("tr", "Turco"),
    ("uk", "Ucraniano"), ("ur", "Urdu"), ("uz", "Uzbeque"),
    ("vi", "Vietnamita"), ("xh", "Xhosa"), ("zh-CN", "Chinês (simpl.)"),
    ("zh-TW", "Chinês (trad.)"), ("zu", "Zulu"),
]


def languages() -> list[dict]:
    return [{"code": code, "name": name} for code, name in LANGUAGES]


# ------------------------------------------------------------- cache

def _load_cache() -> dict:
    global _cache
    if _cache is not None:
        return _cache
    try:
        _cache = json.loads(_cache_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        _cache = {}
    return _cache


def _save_cache() -> None:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        _cache_file.write_text(json.dumps(_cache, ensure_ascii=False),
                               encoding="utf-8")
    except OSError:
        pass


def _key(text: str, target: str) -> str:
    import hashlib
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]
    return f"{target}:{digest}"


# ------------------------------------------------------------- fontes

def _split(text: str, size: int = CHUNK) -> list[str]:
    """Divide respeitando as linhas - letra sem quebra fica ilegivel."""
    chunks, current = [], ""
    for line in text.splitlines(keepends=True):
        if len(current) + len(line) > size and current:
            chunks.append(current)
            current = line
        else:
            current += line
    if current:
        chunks.append(current)
    return chunks


def _mymemory(text: str, target: str, source: str = "auto") -> str | None:
    out = []
    for chunk in _split(text):
        try:
            response = requests.get(
                MYMEMORY,
                params={"q": chunk, "langpair": f"{source}|{target}"},
                timeout=TIMEOUT, headers=_UA,
            )
            data = response.json()
        except (requests.RequestException, ValueError):
            return None

        if str(data.get("responseStatus")) != "200":
            return None
        translated = (data.get("responseData") or {}).get("translatedText")
        if not translated:
            return None
        out.append(translated)
        time.sleep(0.25)   # respeita o servico publico
    return "\n".join(out)


def _ollama(text: str, target_name: str) -> str | None:
    """Reserva local: sem limite diario e sem enviar nada para fora."""
    from . import ai

    if not ai.pick_model():
        return None

    response = ai._generate(
        f"Traduza a letra de musica abaixo para {target_name}.\n"
        "Mantenha uma linha para cada linha original, na mesma ordem.\n"
        "Responda SOMENTE com a traducao, sem comentarios.\n\n"
        f"{text}",
        "Voce e um tradutor de letras de musica. Preserve o sentido e o tom.",
    )
    return (response or "").strip() or None


# ------------------------------------------------------------- publico

def translate(text: str, target: str, source: str = "auto") -> dict:
    """Traduz o texto. Devolve {ok, text, engine}."""
    text = (text or "").strip()
    if not text:
        return {"ok": False, "error": "Nada para traduzir."}

    with _lock:
        cache = _load_cache()
        hit = cache.get(_key(text, target))
    if hit:
        return {"ok": True, "text": hit, "engine": "cache"}

    result = _mymemory(text, target, source)
    engine = "mymemory"

    if not result:
        target_name = dict(LANGUAGES).get(target, target)
        result = _ollama(text, target_name)
        engine = "ollama"

    if not result:
        return {
            "ok": False,
            "error": "Nao consegui traduzir agora. O servico gratuito tem "
                     "limite diario; com o Ollama rodando isso nao acontece.",
        }

    with _lock:
        _load_cache()[_key(text, target)] = result
        _save_cache()

    return {"ok": True, "text": result, "engine": engine}
