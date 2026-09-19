"""Salas de chat entre amigos, sobre o Supabase.

Cada sala tem um codigo curto (APT-7K3F) que funciona como convite: quem tem
o codigo entra, quem nao tem nem descobre que a sala existe.

Dentro da sala da para conversar, ver o que cada um esta ouvindo, mandar
faixas e ligar o "ouvir junto" (todos na mesma musica, no mesmo ponto).

A atualizacao e por polling a cada poucos segundos - simples e suficiente
para um punhado de amigos. O Realtime do Supabase exigiria WebSocket, que
complica o empacotamento sem ganho real nesta escala.
"""

import random
import string
import time

import requests

from . import account

TIMEOUT = 15
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"   # sem I, O, 0, 1

# Diferenca entre o relogio desta maquina e o do servidor, em segundos.
# Sem isso, PCs com horarios diferentes comecariam a musica fora de sincronia.
_clock_offset = 0.0


def _headers() -> dict:
    headers = {
        "apikey": account.SUPABASE_KEY,
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    token = account.load_session().get("access_token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _rest(method: str, table: str, params: dict | None = None,
          payload=None, prefer: str | None = None, retry: bool = True):
    """Chamada REST ao Supabase. Devolve (dados, erro)."""
    if not account.is_configured():
        return None, "Conta nao configurada neste build."
    if not account.current_user():
        return None, "Faca login para usar o chat."

    headers = _headers()
    if prefer:
        headers["Prefer"] = prefer

    try:
        response = requests.request(
            method, f"{account.SUPABASE_URL}/rest/v1/{table}",
            params=params, json=payload, headers=headers, timeout=TIMEOUT,
        )
    except requests.RequestException as exc:
        return None, f"Sem conexao: {exc}"

    if response.status_code == 401 and retry and account.refresh():
        return _rest(method, table, params, payload, prefer, retry=False)

    _learn_clock(response)

    if response.status_code >= 400:
        detail = response.text[:160]
        if "PGRST205" in detail or "does not exist" in detail:
            return None, ("As tabelas do chat ainda nao foram criadas. "
                          "Rode o SQL de CHAT-SQL.md no Supabase.")
        return None, f"Servidor respondeu {response.status_code}: {detail}"

    try:
        return response.json(), None
    except ValueError:
        return [], None


def _learn_clock(response) -> None:
    """Le a hora do servidor no cabecalho Date e guarda a diferenca."""
    global _clock_offset
    header = response.headers.get("Date")
    if not header:
        return
    try:
        from email.utils import parsedate_to_datetime
        server = parsedate_to_datetime(header).timestamp()
    except (TypeError, ValueError):
        return
    # metade do tempo de ida e volta compensa a latencia da resposta
    latency = response.elapsed.total_seconds() / 2 if response.elapsed else 0
    _clock_offset = (server + latency) - time.time()


def server_now() -> float:
    """Hora do servidor, estimada a partir do relogio local."""
    return time.time() + _clock_offset


def clock_offset() -> float:
    return _clock_offset


def _new_code() -> str:
    return "APT-" + "".join(random.choice(_ALPHABET) for _ in range(4))


def _nickname() -> str:
    user = account.current_user() or {}
    email = user.get("email", "")
    return email.split("@")[0][:20] or "alguem"


# ---------------------------------------------------------------- salas

def create(name: str) -> dict:
    user = account.current_user()
    if not user:
        return {"ok": False, "error": "Faca login primeiro."}

    name = (name or "").strip() or "Sala sem nome"

    # colisao de codigo e improvavel, mas tentamos algumas vezes
    for _ in range(5):
        code = _new_code()
        rows, error = _rest("POST", "rooms", payload={
            "code": code, "name": name, "owner_id": user["id"],
        })
        if error and "duplicate" in error.lower():
            continue
        if error:
            return {"ok": False, "error": error}

        room = rows[0] if rows else {}
        join(code)     # o criador ja entra
        return {"ok": True, "id": room.get("id"), "code": code, "name": name}

    return {"ok": False, "error": "Nao consegui gerar um codigo livre."}


def join(code: str) -> dict:
    user = account.current_user()
    if not user:
        return {"ok": False, "error": "Faca login primeiro."}

    code = (code or "").strip().upper()
    if not code.startswith("APT-"):
        code = "APT-" + code.replace("APT", "").strip("- ")

    rows, error = _rest("GET", "rooms", params={
        "code": f"eq.{code}", "select": "id,name,code", "limit": 1,
    })
    if error:
        return {"ok": False, "error": error}
    if not rows:
        return {"ok": False, "error": "Nenhuma sala com esse codigo."}

    room = rows[0]
    _, error = _rest("POST", "room_members", payload={
        "room_id": room["id"], "user_id": user["id"],
        "nickname": _nickname(), "seen_at": "now()",
    }, prefer="resolution=merge-duplicates,return=representation")
    if error:
        return {"ok": False, "error": error}

    return {"ok": True, **room}


def leave(room_id: str) -> dict:
    user = account.current_user()
    if not user:
        return {"ok": False, "error": "Sem sessao."}
    _, error = _rest("DELETE", "room_members", params={
        "room_id": f"eq.{room_id}", "user_id": f"eq.{user['id']}",
    })
    return {"ok": not error, "error": error or ""}


def my_rooms() -> dict:
    user = account.current_user()
    if not user:
        return {"ok": False, "error": "Faca login primeiro.", "rooms": []}

    rows, error = _rest("GET", "room_members", params={
        "user_id": f"eq.{user['id']}",
        "select": "room_id,rooms(id,name,code)",
    })
    if error:
        return {"ok": False, "error": error, "rooms": []}

    rooms = []
    for row in rows or []:
        room = row.get("rooms") or {}
        if room.get("id"):
            rooms.append(room)
    return {"ok": True, "rooms": rooms}


# ---------------------------------------------------------------- presenca

def heartbeat(room_id: str, now_playing: dict | None = None) -> dict:
    """Avisa que continua na sala e o que esta tocando."""
    user = account.current_user()
    if not user:
        return {"ok": False}

    payload = {
        "room_id": room_id, "user_id": user["id"],
        "nickname": _nickname(), "seen_at": "now()",
    }
    if now_playing is not None:
        payload["now_playing"] = now_playing

    _, error = _rest("POST", "room_members", payload=payload,
                     prefer="resolution=merge-duplicates,return=minimal")
    return {"ok": not error}


def members(room_id: str) -> dict:
    rows, error = _rest("GET", "room_members", params={
        "room_id": f"eq.{room_id}",
        "select": "user_id,nickname,now_playing,seen_at",
    })
    if error:
        return {"ok": False, "error": error, "members": []}

    # quem nao da sinal ha 2 minutos conta como offline
    limit = time.time() - 120
    out = []
    for row in rows or []:
        seen = row.get("seen_at") or ""
        online = True
        try:
            from datetime import datetime
            stamp = datetime.fromisoformat(seen.replace("Z", "+00:00"))
            online = stamp.timestamp() > limit
        except (ValueError, AttributeError):
            pass
        out.append({
            "id": row.get("user_id"),
            "nickname": row.get("nickname") or "alguem",
            "now_playing": row.get("now_playing"),
            "online": online,
        })
    return {"ok": True, "members": out}


# ---------------------------------------------------------------- mensagens

def send(room_id: str, body: str = "", track: dict | None = None) -> dict:
    user = account.current_user()
    if not user:
        return {"ok": False, "error": "Faca login primeiro."}
    if not (body or "").strip() and not track:
        return {"ok": False, "error": "Mensagem vazia."}

    _, error = _rest("POST", "messages", payload={
        "room_id": room_id, "user_id": user["id"],
        "nickname": _nickname(), "body": (body or "").strip()[:1000],
        "track": track,
    }, prefer="return=minimal")
    return {"ok": not error, "error": error or ""}


def history(room_id: str, after_id: int = 0, limit: int = 60) -> dict:
    """Mensagens da sala. after_id busca so o que chegou depois."""
    params = {
        "room_id": f"eq.{room_id}",
        "select": "id,user_id,nickname,body,track,created_at",
        "order": "id.desc", "limit": str(limit),
    }
    if after_id:
        params["id"] = f"gt.{after_id}"
        params["order"] = "id.asc"

    rows, error = _rest("GET", "messages", params=params)
    if error:
        return {"ok": False, "error": error, "messages": []}

    messages = rows or []
    if not after_id:
        messages = list(reversed(messages))   # mais antigas primeiro

    user = account.current_user() or {}
    for message in messages:
        message["mine"] = message.get("user_id") == user.get("id")
    return {"ok": True, "messages": messages}


# ---------------------------------------------------------------- ouvir junto

def set_playback(room_id: str, track: dict | None, position: float,
                 playing: bool, start_in: float = 0) -> dict:
    """Atualiza o que a sala esta tocando.

    start_in > 0 agenda o inicio para daqui a tantos segundos - e assim que
    todos comecam no mesmo instante, em vez de cada um na hora que recebe.
    """
    user = account.current_user()
    if not user:
        return {"ok": False, "error": "Sem sessao."}

    payload = {
        "room_id": room_id, "track": track,
        "position": float(position or 0), "playing": bool(playing),
        "updated_by": user["id"], "updated_at": "now()",
    }

    if start_in > 0:
        from datetime import datetime, timezone
        moment = datetime.fromtimestamp(server_now() + start_in, tz=timezone.utc)
        payload["start_at"] = moment.isoformat()
        payload["start_position"] = float(position or 0)

    _, error = _rest("POST", "room_playback", payload=payload,
                     prefer="resolution=merge-duplicates,return=minimal")

    # Bancos sem as colunas novas continuam funcionando, so sem agendamento.
    if error and "start_at" in str(error):
        payload.pop("start_at", None)
        payload.pop("start_position", None)
        _, error = _rest("POST", "room_playback", payload=payload,
                         prefer="resolution=merge-duplicates,return=minimal")

    return {"ok": not error, "error": error or ""}


def get_playback(room_id: str) -> dict:
    select = "track,position,playing,updated_by,updated_at,start_at,start_position"
    rows, error = _rest("GET", "room_playback", params={
        "room_id": f"eq.{room_id}", "select": select, "limit": 1,
    })
    # banco antigo, sem as colunas de agendamento
    if error and "start_at" in str(error):
        rows, error = _rest("GET", "room_playback", params={
            "room_id": f"eq.{room_id}",
            "select": "track,position,playing,updated_by,updated_at", "limit": 1,
        })

    if error:
        return {"ok": False, "error": error}
    if not rows:
        return {"ok": True, "playback": None}

    row = rows[0]
    user = account.current_user() or {}
    row["mine"] = row.get("updated_by") == user.get("id")
    row["server_now"] = server_now()

    from datetime import datetime, timezone

    # Inicio agendado: quanto falta e em que ponto da musica comecar.
    start_at = row.get("start_at")
    if start_at:
        try:
            moment = datetime.fromisoformat(str(start_at).replace("Z", "+00:00"))
            row["starts_in"] = moment.timestamp() - server_now()
            row["start_position"] = float(row.get("start_position") or 0)
        except (ValueError, AttributeError):
            row["starts_in"] = None
    else:
        row["starts_in"] = None

    # Sem agendamento (ou ja passou): posicao corrigida pelo tempo decorrido.
    if row.get("playing") and not (row.get("starts_in") or 0) > 0:
        try:
            base = start_at or row.get("updated_at") or ""
            stamp = datetime.fromisoformat(str(base).replace("Z", "+00:00"))
            elapsed = server_now() - stamp.timestamp()
            origin = (row.get("start_position") if start_at
                      else row.get("position")) or 0
            row["position"] = float(origin) + max(0, elapsed)
        except (ValueError, AttributeError):
            pass

    return {"ok": True, "playback": row}
