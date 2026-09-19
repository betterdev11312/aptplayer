"""Rich Presence no Discord - mostra o que voce esta ouvindo no seu perfil.

Conversa direto com o Discord por um named pipe local (\\\\.\\pipe\\discord-ipc-N),
sem biblioteca externa. Nada sai do computador: o proprio Discord instalado
faz a publicacao.

Se o Discord nao estiver aberto, tudo aqui vira no-op silencioso - o player
nunca deve quebrar por causa disso.

Configuracao: preencha APP_ID com o Application ID do Discord Developer
Portal (veja DISCORD.md). Sem ele, o recurso fica desligado.
"""

import json
import os
import struct
import threading
import time

# Application ID do portal (https://discord.com/developers/applications).
# E publico - aparece no perfil de quem usa o app.
APP_ID = "1550665978030067783"

# Chaves das imagens enviadas em Rich Presence > Art Assets, no portal.
LARGE_IMAGE = "logo"        # capa grande
SMALL_PLAY = "play"         # icone pequeno quando tocando
SMALL_PAUSE = "pause"       # icone pequeno quando pausado

OP_HANDSHAKE = 0
OP_FRAME = 1
OP_CLOSE = 2

_pipe = None
_lock = threading.Lock()
_connected = False
_last_payload: dict | None = None


def is_configured() -> bool:
    return bool(APP_ID)


def _open_pipe():
    """Procura o pipe do Discord. O numero varia conforme instancias abertas."""
    for index in range(10):
        path = rf"\\?\pipe\discord-ipc-{index}"
        try:
            return open(path, "r+b")
        except OSError:
            continue
    return None


def _send(op: int, payload: dict) -> dict | None:
    """Envia um frame e le a resposta. None se falhar."""
    global _pipe, _connected

    if not _pipe:
        return None
    try:
        data = json.dumps(payload).encode("utf-8")
        _pipe.write(struct.pack("<II", op, len(data)) + data)
        _pipe.flush()

        header = _pipe.read(8)
        if len(header) < 8:
            return None
        _, length = struct.unpack("<II", header)
        body = _pipe.read(length)
        return json.loads(body.decode("utf-8"))
    except (OSError, ValueError, struct.error):
        _close()
        return None


def _close() -> None:
    global _pipe, _connected
    if _pipe:
        try:
            _pipe.close()
        except OSError:
            pass
    _pipe = None
    _connected = False


def connect() -> bool:
    """Abre a conexao com o Discord. False se ele nao estiver rodando."""
    global _pipe, _connected

    if not is_configured():
        return False
    with _lock:
        if _connected:
            return True

        _pipe = _open_pipe()
        if not _pipe:
            return False

        response = _send(OP_HANDSHAKE, {"v": 1, "client_id": APP_ID})
        if not response or response.get("evt") == "ERROR":
            _close()
            return False

        _connected = True
        return True


def disconnect() -> None:
    with _lock:
        if _connected:
            _send(OP_CLOSE, {})
        _close()


def is_connected() -> bool:
    return _connected


def set_activity(track: dict | None, playing: bool = True,
                 position: float = 0, duration: float = 0) -> bool:
    """Atualiza o status. track=None limpa a presenca."""
    global _last_payload

    if not is_configured():
        return False
    if not _connected and not connect():
        return False

    if not track:
        payload = {
            "cmd": "SET_ACTIVITY",
            "args": {"pid": os.getpid(), "activity": None},
            "nonce": str(time.time()),
        }
        with _lock:
            _send(OP_FRAME, payload)
            _last_payload = None
        return True

    title = (track.get("title") or "Musica")[:128]
    artist = (track.get("artist") or "")[:128]

    activity = {
        "type": 2,                       # 2 = "Ouvindo"
        "details": title,
        "state": f"por {artist}" if artist else "AptPlayer",
        "assets": {
            "large_image": LARGE_IMAGE,
            "large_text": "AptPlayer",
            "small_image": SMALL_PLAY if playing else SMALL_PAUSE,
            "small_text": "tocando" if playing else "pausado",
        },
    }

    # Barra de progresso: o Discord calcula a partir dos horarios de inicio
    # e fim, entao so faz sentido quando a musica esta correndo.
    if playing and duration > 0:
        now = time.time()
        activity["timestamps"] = {
            "start": int((now - position) * 1000),
            "end": int((now - position + duration) * 1000),
        }

    video_id = track.get("video_id")
    if video_id:
        activity["buttons"] = [{
            "label": "Ouvir no YouTube",
            "url": f"https://www.youtube.com/watch?v={video_id}",
        }]

    payload = {
        "cmd": "SET_ACTIVITY",
        "args": {"pid": os.getpid(), "activity": activity},
        "nonce": str(time.time()),
    }

    # Evita reenviar identico: o Discord limita a ~5 atualizacoes por 20s.
    signature = json.dumps(activity, sort_keys=True)
    with _lock:
        if signature == _last_payload:
            return True
        result = _send(OP_FRAME, payload)
        _last_payload = signature if result else None
    return bool(result)


def status() -> dict:
    return {
        "configured": is_configured(),
        "connected": _connected,
        "discord_running": _open_pipe() is not None if is_configured() else False,
    }
