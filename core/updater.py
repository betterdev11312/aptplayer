"""Verificacao de atualizacao.

O app consulta um arquivo version.json publicado junto com o site e avisa
quando existe versao nova. Nao baixa nem instala sozinho: abre a pagina de
download e deixa a decisao com o usuario.
"""

import json
import threading

import requests

from .paths import DATA_DIR

VERSION = "1.9.0"

# Site do projeto (Cloudflare Workers). Deixe vazio para desligar a verificacao.
SITE_URL = "https://betterdev11312.github.io/aptplayer"
UPDATE_URL = f"{SITE_URL}/version.json" if SITE_URL else ""
TIMEOUT = 8

_state_file = DATA_DIR / "update.json"
_lock = threading.Lock()


def _parse(version: str) -> tuple:
    """'1.10.2' -> (1, 10, 2); compara corretamente 1.10 > 1.9."""
    parts = []
    for chunk in str(version or "0").split("."):
        digits = "".join(c for c in chunk if c.isdigit())
        parts.append(int(digits) if digits else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def is_newer(remote: str, local: str = VERSION) -> bool:
    return _parse(remote) > _parse(local)


def _read_state() -> dict:
    try:
        return json.loads(_state_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _write_state(data: dict) -> None:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        _state_file.write_text(json.dumps(data), encoding="utf-8")
    except OSError:
        pass


def check() -> dict:
    """Consulta o servidor. Sempre devolve dict, nunca levanta.

    O campo 'reason' diz POR QUE falhou, para a interface nao chutar a causa:
      not_configured | offline | not_published | bad_response
    """
    result = {
        "ok": True,
        "current": VERSION,
        "latest": VERSION,
        "update": False,
        "notes": "",
        "url": "",
        "exe": "",
        "reason": "",
    }

    if not UPDATE_URL:
        result["ok"] = False
        result["reason"] = "not_configured"
        return result

    try:
        response = requests.get(
            UPDATE_URL, timeout=TIMEOUT,
            headers={"User-Agent": f"AptPlayer/{VERSION}"},
        )
    except requests.RequestException:
        result["ok"] = False
        result["reason"] = "offline"
        return result

    if response.status_code == 404:
        # O site existe, mas ainda nao tem version.json publicado.
        result["ok"] = False
        result["reason"] = "not_published"
        return result

    try:
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        result["ok"] = False
        result["reason"] = "bad_response"
        return result

    latest = str(data.get("version", VERSION))
    result["latest"] = latest
    result["notes"] = str(data.get("notes", ""))
    result["url"] = str(data.get("url", ""))
    # link do .exe puro: e o que a atualizacao automatica substitui
    result["exe"] = str(data.get("exe", ""))
    result["update"] = is_newer(latest)
    return result


def check_async(callback) -> None:
    """Consulta em background; chama callback(resultado)."""
    def run():
        try:
            callback(check())
        except Exception:
            pass
    threading.Thread(target=run, daemon=True).start()


def snooze(version: str) -> None:
    """Marca esta versao como 'lembrar depois'."""
    with _lock:
        state = _read_state()
        state["skipped"] = version
        _write_state(state)


def is_snoozed(version: str) -> bool:
    return _read_state().get("skipped") == version
