"""Conta e sincronizacao via Supabase (plano gratuito).

O AptPlayer continua funcionando 100% sem conta. Quem criar uma ganha:
 - biblioteca, favoritas e playlists salvas na nuvem
 - recuperar tudo em outro PC ou depois de formatar

Nada e enviado automaticamente: a sincronizacao e sempre uma acao do usuario.

Configuracao: preencha SUPABASE_URL e SUPABASE_KEY abaixo (veja SUPABASE.md).
A chave 'anon' e publica por design - o que protege os dados e a policy de
Row Level Security, que o SUPABASE.md manda criar.
"""

import json
import threading
import time

import requests

from .paths import DATA_DIR

# ---------------------------------------------------------------- config
SUPABASE_URL = ""      # ex.: https://abcdefgh.supabase.co
SUPABASE_KEY = ""      # a chave "anon public" do painel
TIMEOUT = 20

_session_file = DATA_DIR / "session.json"
_lock = threading.Lock()
_session: dict = {}


def is_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


# ---------------------------------------------------------------- sessao

def _save_session(data: dict) -> None:
    global _session
    with _lock:
        _session = data or {}
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            _session_file.write_text(json.dumps(_session), encoding="utf-8")
        except OSError:
            pass


def load_session() -> dict:
    global _session
    if _session:
        return _session
    try:
        _session = json.loads(_session_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        _session = {}
    return _session


def logout() -> None:
    _save_session({})
    try:
        _session_file.unlink(missing_ok=True)
    except OSError:
        pass


def current_user() -> dict | None:
    session = load_session()
    if not session.get("access_token"):
        return None
    return {
        "email": session.get("email", ""),
        "id": session.get("user_id", ""),
        "since": session.get("since", 0),
    }


def _headers(auth: bool = True) -> dict:
    headers = {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json",
    }
    if auth:
        token = load_session().get("access_token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
    return headers


# ------------------------------------------------------------- auth

def _auth_call(path: str, payload: dict) -> dict:
    if not is_configured():
        return {"ok": False, "error": "Conta nao configurada neste build."}
    try:
        response = requests.post(
            f"{SUPABASE_URL}/auth/v1/{path}",
            json=payload, headers=_headers(auth=False), timeout=TIMEOUT,
        )
        data = response.json()
    except requests.RequestException as exc:
        return {"ok": False, "error": f"Sem conexao: {exc}"}
    except ValueError:
        return {"ok": False, "error": "Resposta invalida do servidor."}

    if response.status_code >= 400:
        message = data.get("msg") or data.get("error_description") \
            or data.get("message") or "Falha na autenticacao."
        return {"ok": False, "error": message}
    return {"ok": True, "data": data}


def sign_up(email: str, password: str) -> dict:
    result = _auth_call("signup", {"email": email, "password": password})
    if not result["ok"]:
        return result

    data = result["data"]
    # Com confirmacao de email ligada, ainda nao vem token.
    if not data.get("access_token"):
        return {"ok": True, "needs_confirmation": True,
                "message": "Conta criada. Confirme pelo link no seu email."}

    _store_login(data, email)
    return {"ok": True, "email": email}


def sign_in(email: str, password: str) -> dict:
    result = _auth_call("token?grant_type=password",
                        {"email": email, "password": password})
    if not result["ok"]:
        return result
    _store_login(result["data"], email)
    return {"ok": True, "email": email}


def _store_login(data: dict, email: str) -> None:
    user = data.get("user") or {}
    _save_session({
        "access_token": data.get("access_token", ""),
        "refresh_token": data.get("refresh_token", ""),
        "user_id": user.get("id", ""),
        "email": user.get("email", email),
        "since": int(time.time()),
    })


def refresh() -> bool:
    """Renova o token expirado. True se conseguiu."""
    session = load_session()
    token = session.get("refresh_token")
    if not token:
        return False
    result = _auth_call("token?grant_type=refresh_token",
                        {"refresh_token": token})
    if not result["ok"]:
        return False
    _store_login(result["data"], session.get("email", ""))
    return True


# ------------------------------------------------------------- sync

TABLE = "libraries"


def _rest(method: str, params: dict | None = None, payload=None,
          retry: bool = True):
    url = f"{SUPABASE_URL}/rest/v1/{TABLE}"
    headers = _headers()
    headers["Prefer"] = "resolution=merge-duplicates,return=representation"
    try:
        response = requests.request(
            method, url, params=params, json=payload,
            headers=headers, timeout=TIMEOUT,
        )
    except requests.RequestException as exc:
        return None, f"Sem conexao: {exc}"

    # token expirado: renova uma vez e tenta de novo
    if response.status_code == 401 and retry and refresh():
        return _rest(method, params, payload, retry=False)

    if response.status_code >= 400:
        return None, f"Servidor respondeu {response.status_code}: {response.text[:120]}"
    try:
        return response.json(), None
    except ValueError:
        return [], None


def upload(snapshot: dict) -> dict:
    """Envia a biblioteca inteira (substitui o que estava la)."""
    user = current_user()
    if not user:
        return {"ok": False, "error": "Faca login primeiro."}

    payload = {
        "user_id": user["id"],
        "data": snapshot,
        "updated_at": "now()",
    }
    _, error = _rest("POST", payload=payload)
    if error:
        return {"ok": False, "error": error}
    return {"ok": True, "tracks": len(snapshot.get("tracks", []))}


def download() -> dict:
    """Baixa a biblioteca salva na nuvem."""
    user = current_user()
    if not user:
        return {"ok": False, "error": "Faca login primeiro."}

    rows, error = _rest("GET", params={
        "user_id": f"eq.{user['id']}", "select": "data,updated_at", "limit": 1,
    })
    if error:
        return {"ok": False, "error": error}
    if not rows:
        return {"ok": False, "error": "Nenhum backup salvo nesta conta ainda."}

    row = rows[0]
    return {"ok": True, "data": row.get("data") or {},
            "updated_at": row.get("updated_at", "")}
