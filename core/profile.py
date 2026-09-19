"""Perfil do usuario: nickname, foto e bio.

Fica no Supabase junto da conta, entao aparece para os amigos nas salas e
acompanha voce ao trocar de PC.

A foto vai como data URL dentro do proprio perfil - imagens pequenas (o app
reduz para 256px) cabem bem e evitam configurar um bucket de storage.
"""

import base64
import io
import re

import requests

from . import account

TIMEOUT = 20
MAX_AVATAR = 256          # pixels; o suficiente para a lista de membros
MAX_BYTES = 90_000        # limite do data URL guardado

_cache: dict[str, dict] = {}


def _headers() -> dict:
    headers = {
        "apikey": account.SUPABASE_KEY,
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=representation",
    }
    token = account.load_session().get("access_token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _rest(method: str, params: dict | None = None, payload=None,
          retry: bool = True):
    if not account.is_configured():
        return None, "Conta nao configurada neste build."

    try:
        response = requests.request(
            method, f"{account.SUPABASE_URL}/rest/v1/profiles",
            params=params, json=payload, headers=_headers(), timeout=TIMEOUT,
        )
    except requests.RequestException as exc:
        return None, f"Sem conexao: {exc}"

    if response.status_code == 401 and retry and account.refresh():
        return _rest(method, params, payload, retry=False)

    if response.status_code >= 400:
        detail = response.text[:160]
        if "PGRST205" in detail or "does not exist" in detail:
            return None, ("A tabela de perfis ainda nao existe. "
                          "Rode o SQL de PERFIS-SQL.md no Supabase.")
        return None, f"Servidor respondeu {response.status_code}: {detail}"

    try:
        return response.json(), None
    except ValueError:
        return [], None


def _default_nickname() -> str:
    user = account.current_user() or {}
    return (user.get("email", "").split("@")[0] or "alguem")[:24]


def get(user_id: str = "") -> dict:
    """Perfil de alguem. Sem argumento, o seu."""
    if not user_id:
        user = account.current_user()
        if not user:
            return {"ok": False, "error": "Faca login primeiro."}
        user_id = user["id"]

    if user_id in _cache:
        return {"ok": True, "profile": _cache[user_id]}

    rows, error = _rest("GET", params={
        "user_id": f"eq.{user_id}",
        "select": "user_id,nickname,avatar,bio,updated_at", "limit": 1,
    })
    if error:
        return {"ok": False, "error": error}

    if not rows:
        # perfil ainda nao criado: devolve um padrao, sem gravar nada
        return {"ok": True, "profile": {
            "user_id": user_id, "nickname": _default_nickname(),
            "avatar": "", "bio": "", "new": True,
        }}

    _cache[user_id] = rows[0]
    return {"ok": True, "profile": rows[0]}


def save(nickname: str = "", bio: str = "", avatar: str | None = None) -> dict:
    """Salva o proprio perfil. avatar=None mantem a foto atual."""
    user = account.current_user()
    if not user:
        return {"ok": False, "error": "Faca login primeiro."}

    nickname = (nickname or "").strip()[:24] or _default_nickname()
    bio = (bio or "").strip()[:200]

    payload = {
        "user_id": user["id"],
        "nickname": nickname,
        "bio": bio,
        "updated_at": "now()",
    }
    if avatar is not None:
        payload["avatar"] = avatar

    rows, error = _rest("POST", payload=payload)
    if error:
        return {"ok": False, "error": error}

    _cache.pop(user["id"], None)
    return {"ok": True, "profile": (rows or [payload])[0]}


def many(user_ids: list[str]) -> dict:
    """Perfis de varias pessoas - usado na lista de membros da sala."""
    ids = [u for u in (user_ids or []) if u]
    if not ids:
        return {"ok": True, "profiles": {}}

    lista = ",".join(ids)
    rows, error = _rest("GET", params={
        "user_id": f"in.({lista})",
        "select": "user_id,nickname,avatar,bio",
    })
    if error:
        return {"ok": False, "error": error, "profiles": {}}

    perfis = {row["user_id"]: row for row in rows or []}
    _cache.update(perfis)
    return {"ok": True, "profiles": perfis}


def prepare_avatar(path: str) -> dict:
    """Le uma imagem do disco e devolve um data URL pequeno o bastante."""
    try:
        from PIL import Image
    except ImportError:
        return {"ok": False, "error": "Pillow nao disponivel neste build."}

    try:
        image = Image.open(path).convert("RGB")
    except (OSError, ValueError) as exc:
        return {"ok": False, "error": f"Imagem invalida: {exc}"}

    # recorta quadrado no centro e reduz
    width, height = image.size
    side = min(width, height)
    image = image.crop((
        (width - side) // 2, (height - side) // 2,
        (width + side) // 2, (height + side) // 2,
    )).resize((MAX_AVATAR, MAX_AVATAR), Image.LANCZOS)

    # cai a qualidade ate caber no limite
    for quality in (85, 70, 55, 40):
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=quality, optimize=True)
        data = buffer.getvalue()
        if len(data) <= MAX_BYTES:
            encoded = base64.b64encode(data).decode("ascii")
            return {"ok": True, "avatar": f"data:image/jpeg;base64,{encoded}"}

    return {"ok": False, "error": "Nao consegui reduzir a imagem o bastante."}
