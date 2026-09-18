r"""Onde ficam os dados do app.

Rodando pelo codigo (.py), tudo fica na pasta do projeto - pratico para
desenvolver. Empacotado (.exe), vai para %LOCALAPPDATA%\AptPlayer, porque a
pasta do executavel pode ser somente leitura (ex.: Program Files).
"""

import os
import sys
from pathlib import Path

FROZEN = getattr(sys, "frozen", False)


def _base_dir() -> Path:
    if FROZEN:
        local = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return Path(local) / "AptPlayer"
    return Path(__file__).resolve().parent.parent


def resource_dir() -> Path:
    """Arquivos somente leitura que viajam junto (ui/, icon/)."""
    if FROZEN:
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent


DATA_DIR = _base_dir() / "data"
CACHE_DIR = DATA_DIR / "cache"
COVERS_DIR = DATA_DIR / "covers"
DB_PATH = DATA_DIR / "library.db"


def ensure_dirs() -> None:
    for folder in (DATA_DIR, CACHE_DIR, COVERS_DIR):
        folder.mkdir(parents=True, exist_ok=True)
