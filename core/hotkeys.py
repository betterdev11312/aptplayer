"""Teclas de midia globais - funcionam com o app minimizado.

Registra as teclas do teclado (play/pause, proxima, anterior, stop) direto no
Windows via RegisterHotKey. Sem dependencia externa: so ctypes.

Se outro programa ja tiver registrado a mesma tecla, o registro falha em
silencio - e o comportamento correto, quem pediu primeiro fica com ela.
"""

import ctypes
import threading
from ctypes import wintypes

user32 = ctypes.windll.user32

WM_HOTKEY = 0x0312
WM_QUIT = 0x0012

# Teclas de midia dos teclados
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3

HOTKEYS = {
    1: (0, VK_MEDIA_PLAY_PAUSE, "playpause"),
    2: (0, VK_MEDIA_NEXT_TRACK, "next"),
    3: (0, VK_MEDIA_PREV_TRACK, "prev"),
    4: (0, VK_MEDIA_STOP, "stop"),
}

_thread: threading.Thread | None = None
_thread_id = 0
_running = False


def _loop(callback) -> None:
    """Thread propria: RegisterHotKey exige um message loop."""
    global _thread_id, _running

    _thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
    registered = []

    for hotkey_id, (modifiers, vk, _action) in HOTKEYS.items():
        if user32.RegisterHotKey(None, hotkey_id, modifiers, vk):
            registered.append(hotkey_id)

    if not registered:
        _running = False
        return

    _running = True
    message = wintypes.MSG()
    try:
        while _running and user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
            if message.message == WM_HOTKEY:
                entry = HOTKEYS.get(message.wParam)
                if entry:
                    try:
                        callback(entry[2])
                    except Exception:
                        pass  # erro no callback nao derruba o loop
    finally:
        for hotkey_id in registered:
            user32.UnregisterHotKey(None, hotkey_id)
        _running = False


def start(callback) -> bool:
    """Liga as teclas globais. callback(acao) com play/next/prev/stop."""
    global _thread
    if _thread and _thread.is_alive():
        return True
    _thread = threading.Thread(target=_loop, args=(callback,), daemon=True)
    _thread.start()
    # da um instante para o registro acontecer
    import time
    time.sleep(0.3)
    return _running


def stop() -> None:
    global _running
    _running = False
    if _thread_id:
        ctypes.windll.user32.PostThreadMessageW(_thread_id, WM_QUIT, 0, 0)


def is_active() -> bool:
    return _running
