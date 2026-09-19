"""Publica um Release no GitHub sem passar pelo navegador.

O upload pelo site falha com frequencia em arquivos grandes. Aqui o envio e
feito direto pela API, com repeticao automatica se cair no meio.

Uso:
    python tools_release.py                 # usa a versao de core/updater.py
    python tools_release.py 1.7.0           # forca uma versao

Precisa de um token do GitHub na primeira vez - o script explica como pegar.
"""

import json
import os
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
OWNER = "betterdev11312"
REPO = "aptplayer"
TOKEN_FILE = ROOT / ".github-token"

FILES = [
    "AptPlayer-Setup.exe",
    "AptPlayer-Setup.zip",
    "AptPlayer.exe",
    "AptPlayer.zip",
]


def version() -> str:
    if len(sys.argv) > 1:
        return sys.argv[1].lstrip("v")
    text = (ROOT / "core" / "updater.py").read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("VERSION ="):
            return line.split('"')[1]
    return "1.0.0"


def token() -> str:
    """Le o token salvo, ou pede uma vez e guarda."""
    env = os.environ.get("GITHUB_TOKEN")
    if env:
        return env.strip()

    if TOKEN_FILE.exists():
        saved = TOKEN_FILE.read_text(encoding="utf-8").strip()
        if saved:
            return saved

    print()
    print("Preciso de um token do GitHub (uma vez so).")
    print()
    print("1. Abra: https://github.com/settings/tokens/new")
    print("2. Note: aptplayer-release")
    print("3. Expiration: 90 days (ou o que preferir)")
    print("4. Marque a caixa 'repo'")
    print("5. Generate token e copie (comeca com ghp_)")
    print()
    value = input("Cole o token aqui: ").strip()
    if not value:
        print("Sem token, nao da para publicar.")
        sys.exit(1)

    TOKEN_FILE.write_text(value, encoding="utf-8")
    print(f"Guardado em {TOKEN_FILE.name} (ja esta no .gitignore)")
    return value


def headers(tok: str) -> dict:
    return {
        "Authorization": f"Bearer {tok}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def notes() -> str:
    path = ROOT / "RELEASE-NOTES.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def find_release(tok: str, tag: str) -> dict | None:
    response = requests.get(
        f"https://api.github.com/repos/{OWNER}/{REPO}/releases/tags/{tag}",
        headers=headers(tok), timeout=30,
    )
    return response.json() if response.status_code == 200 else None


def create_release(tok: str, tag: str) -> dict:
    response = requests.post(
        f"https://api.github.com/repos/{OWNER}/{REPO}/releases",
        headers=headers(tok), timeout=30,
        json={
            "tag_name": tag,
            "name": f"AptPlayer {tag.lstrip('v')}",
            "body": notes(),
            "draft": False,
            "prerelease": False,
        },
    )
    if response.status_code >= 400:
        print("Falha ao criar o release:", response.status_code, response.text[:300])
        sys.exit(1)
    return response.json()


def delete_asset(tok: str, asset_id: int) -> None:
    requests.delete(
        f"https://api.github.com/repos/{OWNER}/{REPO}/releases/assets/{asset_id}",
        headers=headers(tok), timeout=30,
    )


def upload(tok: str, release: dict, path: Path, tries: int = 3) -> bool:
    """Envia um arquivo, repetindo se a conexao cair."""
    # remove versao anterior do mesmo arquivo, se houver
    for asset in release.get("assets", []):
        if asset["name"] == path.name:
            delete_asset(tok, asset["id"])

    url = release["upload_url"].split("{")[0] + f"?name={path.name}"
    size_mb = path.stat().st_size / 1024 / 1024

    for attempt in range(1, tries + 1):
        print(f"  {path.name} ({size_mb:.1f} MB) tentativa {attempt}...", end=" ", flush=True)
        try:
            with open(path, "rb") as fh:
                response = requests.post(
                    url, headers={**headers(tok),
                                  "Content-Type": "application/octet-stream"},
                    data=fh, timeout=600,
                )
            if response.status_code < 400:
                print("OK")
                return True
            print(f"falhou ({response.status_code})")
            if response.status_code == 422:      # ja existe
                print("    (arquivo ja estava la)")
                return True
        except requests.RequestException as exc:
            print(f"erro de rede: {str(exc)[:60]}")
        time.sleep(3)

    return False


def main() -> None:
    ver = version()
    tag = f"v{ver}"
    tok = token()

    missing = [f for f in FILES if not (ROOT / "site" / f).exists()]
    if missing:
        print("Faltam arquivos em site/:", ", ".join(missing))
        print("Rode: python -m PyInstaller ... && python tools_package.py")
        sys.exit(1)

    print(f"\nPublicando {tag}...")
    release = find_release(tok, tag)
    if release:
        print("  release ja existe, atualizando os arquivos")
    else:
        release = create_release(tok, tag)
        print("  release criado")

    ok = True
    for name in FILES:
        if not upload(tok, release, ROOT / "site" / name):
            ok = False

    print()
    if ok:
        print(f"Pronto: https://github.com/{OWNER}/{REPO}/releases/tag/{tag}")
        print("Quem estiver numa versao antiga ja vai ver a atualizacao.")
    else:
        print("Algum arquivo falhou. Rode de novo - ele continua de onde parou.")


if __name__ == "__main__":
    main()
