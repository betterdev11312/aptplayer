"""Gera os .zip dos executaveis para anexar ao Release."""
import zipfile
from pathlib import Path

DIST = Path("dist")
OUT = Path("site")

for exe in ("AptPlayer.exe", "AptPlayer-Setup.exe"):
    source = DIST / exe
    if not source.exists():
        print(f"  {exe}: nao encontrado (compile primeiro)")
        continue

    # copia o .exe solto tambem, para quem preferir baixar direto
    (OUT / exe).write_bytes(source.read_bytes())

    target = OUT / exe.replace(".exe", ".zip")
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.write(source, exe)
    print(f"  {target.name}: {target.stat().st_size / 1024 / 1024:.1f} MB")
