"""Atualizacao automatica, como Discord e Spotify fazem.

O app baixa a versao nova em background, mostra o progresso e se substitui
sozinho. O usuario so clica em "Atualizar".

Como a troca funciona no Windows: um .exe em execucao nao pode ser
sobrescrito, mas PODE ser renomeado. Entao:

  1. baixa o novo para <nome>.new
  2. renomeia o atual para <nome>.old
  3. renomeia o novo para <nome>
  4. inicia o novo e fecha o antigo
  5. na proxima abertura, o .old e apagado

Se algo falhar no meio, o passo 3 desfaz o passo 2 e o app continua
funcionando com a versao antiga.
"""

import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import requests

from . import updater

TIMEOUT = 30
_lock = threading.Lock()

_state = {
    "running": False, "done": False, "ok": False,
    "step": "", "percent": 0, "error": "", "version": "",
}


def current_exe() -> Path | None:
    """Caminho do executavel rodando. None se estiver rodando pelo codigo."""
    if not getattr(sys, "frozen", False):
        return None
    return Path(sys.executable)


def can_auto_update() -> bool:
    """So faz sentido no .exe empacotado e com pasta gravavel."""
    exe = current_exe()
    if not exe:
        return False
    return os.access(exe.parent, os.W_OK)


def cleanup_old() -> None:
    """Apaga o executavel antigo deixado pela atualizacao anterior."""
    exe = current_exe()
    if not exe:
        return
    old = exe.with_suffix(exe.suffix + ".old")
    if old.exists():
        try:
            old.unlink()
        except OSError:
            pass  # ainda travado; tenta na proxima vez


def state() -> dict:
    with _lock:
        return dict(_state)


def _set(**kw) -> None:
    with _lock:
        _state.update(kw)


def start(url: str, version: str) -> dict:
    """Dispara o download em background."""
    if not can_auto_update():
        return {
            "ok": False,
            "error": "A atualizacao automatica so funciona no app instalado.",
        }

    with _lock:
        if _state["running"]:
            return {"ok": True, "started": False}
        _state.update({
            "running": True, "done": False, "ok": False,
            "step": "conectando...", "percent": 0, "error": "",
            "version": version,
        })

    threading.Thread(target=_run, args=(url, version), daemon=True).start()
    return {"ok": True, "started": True}


def _run(url: str, version: str) -> None:
    exe = current_exe()
    new_file = exe.with_suffix(exe.suffix + ".new")

    try:
        _set(step="baixando a nova versao...", percent=2)

        with requests.get(url, stream=True, timeout=TIMEOUT,
                          headers={"User-Agent": f"AptPlayer/{updater.VERSION}"}) as response:
            response.raise_for_status()
            total = int(response.headers.get("content-length") or 0)
            written = 0

            with open(new_file, "wb") as out:
                for chunk in response.iter_content(256 * 1024):
                    if not chunk:
                        continue
                    out.write(chunk)
                    written += len(chunk)
                    if total:
                        _set(percent=2 + int(written / total * 88))

        if new_file.stat().st_size < 1_000_000:
            raise OSError("o arquivo baixado parece incompleto")

        _set(step="instalando...", percent=94)
        _swap(exe, new_file)

        _set(step="reiniciando...", percent=99)
        subprocess.Popen([str(exe)], cwd=str(exe.parent))
        time.sleep(0.6)

        _set(running=False, done=True, ok=True, percent=100, step="pronto")
        # da tempo da interface mostrar "pronto" antes de fechar
        threading.Timer(1.2, lambda: os._exit(0)).start()

    except Exception as exc:
        try:
            new_file.unlink(missing_ok=True)
        except OSError:
            pass
        _set(running=False, done=True, ok=False,
             error=f"Nao consegui atualizar: {exc}")


def _swap(exe: Path, new_file: Path) -> None:
    """Troca o executavel, desfazendo se algo der errado."""
    old = exe.with_suffix(exe.suffix + ".old")

    if old.exists():
        try:
            old.unlink()
        except OSError:
            pass

    # um .exe em uso nao pode ser sobrescrito, mas pode ser renomeado
    exe.rename(old)
    try:
        new_file.rename(exe)
    except OSError:
        old.rename(exe)   # volta ao estado anterior
        raise
