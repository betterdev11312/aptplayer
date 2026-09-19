"""Instalador do AptPlayer.

Um .exe pequeno que copia o player para a pasta do usuario, cria atalhos e
registra a desinstalacao no Painel de Controle. Sem dependencia de NSIS ou
Inno Setup: e o mesmo PyInstaller que ja empacota o app.

Build:
    python -m PyInstaller installer.spec --noconfirm --clean
"""

import os
import shutil
import subprocess
import sys
import threading
import time
import winreg
from pathlib import Path

import webview

APP_NAME = "AptPlayer"
APP_VERSION = "1.7.0"
PUBLISHER = "AptPlayer"
EXE_NAME = "AptPlayer.exe"
REG_KEY = rf"Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME}"


def _trace(msg: str) -> None:
    """Marca o progresso num arquivo - o console nao aparece no modo windowed."""
    try:
        import tempfile
        path = Path(tempfile.gettempdir()) / "aptplayer_setup_trace.log"
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(time.strftime("%H:%M:%S") + " " + msg + chr(10))
    except Exception:
        pass


def resource(name: str) -> Path:
    """Arquivo embutido no instalador.

    Empacotado, vem de sys._MEIPASS. Rodando pelo codigo, procura tambem em
    dist/ e icon/, para dar para testar sem compilar.
    """
    bundled = getattr(sys, "_MEIPASS", None)
    if bundled:
        return Path(bundled) / name

    root = Path(__file__).resolve().parent
    for candidate in (root / name, root / "dist" / name, root / "icon" / name):
        if candidate.exists():
            return candidate
    return root / name


def install_dir() -> Path:
    local = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return Path(local) / "Programs" / APP_NAME


def _make_shortcuts(target: Path, links: list[Path],
                    icon: Path | None = None) -> int:
    """Cria varios atalhos numa CHAMADA SO de PowerShell.

    Cada invocacao do PowerShell custa 1-3s; fazer uma por atalho era metade
    da lentidao percebida.
    """
    if not links:
        return 0

    icon_line = f'$s.IconLocation = "{icon}";' if icon else ""
    parts = ['$w = New-Object -ComObject WScript.Shell;']
    for link in links:
        parts.append(
            f'$s = $w.CreateShortcut("{link}"); '
            f'$s.TargetPath = "{target}"; '
            f'$s.WorkingDirectory = "{target.parent}"; '
            f'{icon_line} '
            f'$s.Save();'
        )
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive",
             "-ExecutionPolicy", "Bypass", "-Command", " ".join(parts)],
            check=True, capture_output=True, timeout=40,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (subprocess.SubprocessError, OSError):
        return 0
    return sum(1 for link in links if link.exists())


def register_uninstall(target: Path, size_kb: int) -> None:
    """Faz o app aparecer em Aplicativos Instalados."""
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_KEY) as key:
            values = {
                "DisplayName": APP_NAME,
                "DisplayVersion": APP_VERSION,
                "Publisher": PUBLISHER,
                "DisplayIcon": str(target),
                "InstallLocation": str(target.parent),
                "UninstallString": f'"{target.parent / "uninstall.bat"}"',
                "NoModify": 1,
                "NoRepair": 1,
                "EstimatedSize": size_kb,
            }
            for name, value in values.items():
                kind = winreg.REG_DWORD if isinstance(value, int) else winreg.REG_SZ
                winreg.SetValueEx(key, name, 0, kind, value)
    except OSError:
        pass


def write_uninstaller(folder: Path) -> None:
    """Desinstalador simples: apaga a pasta e a chave do registro."""
    lines = [
        "@echo off",
        f"echo Desinstalando {APP_NAME}...",
        f"taskkill /F /IM {EXE_NAME} >nul 2>&1",
        "timeout /t 1 /nobreak >nul",
        f'reg delete "HKCU\\{REG_KEY}" /f >nul 2>&1',
        f'del "%USERPROFILE%\\Desktop\\{APP_NAME}.lnk" >nul 2>&1',
        f'del "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\'
        f'{APP_NAME}.lnk" >nul 2>&1',
        "echo.",
        "echo Seus dados (musicas e playlists) NAO foram apagados.",
        f"echo Eles ficam em: %LOCALAPPDATA%\\{APP_NAME}",
        "echo.",
        "pause",
        # A pasta so pode ser removida depois que este .bat terminar.
        f'start "" cmd /c "timeout /t 2 /nobreak >nul & rmdir /s /q ""{folder}"""',
    ]
    try:
        (folder / "uninstall.bat").write_text("\n".join(lines), encoding="utf-8")
    except OSError:
        pass


# A janela fica FORA da classe: qualquer atributo da API e inspecionado pelo
# pywebview, e um objeto nativo ali trava a interface com recursao infinita.
_window = None


class InstallerApi:
    """Ponte com a interface do instalador."""

    def __init__(self):
        self._lock = threading.Lock()
        self._progress = {
            "running": False, "done": False, "ok": False,
            "step": "", "percent": 0, "error": "", "shortcuts": [],
        }

    def get_info(self) -> dict:
        _trace("get_info chamado")
        return {
            "name": APP_NAME,
            "version": APP_VERSION,
            "path": str(install_dir()),
            "installed": (install_dir() / EXE_NAME).exists(),
        }

    def install(self, desktop: bool = True, start_menu: bool = True,
                launch: bool = True) -> dict:
        """Dispara a instalacao em background e volta na hora.

        A interface acompanha por progress(); se este metodo fizesse o
        trabalho, a janela congelaria durante a copia.
        """
        with self._lock:
            if self._progress["running"]:
                return {"ok": True, "started": False}
            self._progress = {
                "running": True, "done": False, "ok": False,
                "step": "preparando...", "percent": 0,
                "error": "", "shortcuts": [],
            }

        threading.Thread(
            target=self._run_install,
            args=(bool(desktop), bool(start_menu), bool(launch)),
            daemon=True,
        ).start()
        return {"ok": True, "started": True}

    def progress(self) -> dict:
        """Estado atual da instalacao (a interface consulta a cada 200ms)."""
        with self._lock:
            return dict(self._progress)

    def _set(self, **kw) -> None:
        with self._lock:
            self._progress.update(kw)

    def _run_install(self, desktop: bool, start_menu: bool, launch: bool) -> None:
        try:
            source = resource(EXE_NAME)
            if not source.exists():
                self._set(running=False, done=True, ok=False,
                          error=f"{EXE_NAME} nao veio junto no instalador.")
                return

            target_dir = install_dir()
            target = target_dir / EXE_NAME

            self._set(step="fechando versao anterior...", percent=8)
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", EXE_NAME],
                    capture_output=True, timeout=10,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                time.sleep(0.4)   # o Windows leva um instante para soltar o arquivo
            except (subprocess.SubprocessError, OSError):
                pass

            self._set(step="copiando arquivos...", percent=15)
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
                self._copy_with_progress(source, target)
            except OSError as exc:
                self._set(running=False, done=True, ok=False,
                          error=f"Nao consegui copiar: {exc}")
                return

            icon = resource("app.ico")
            if icon.exists():
                try:
                    shutil.copy2(icon, target_dir / "app.ico")
                    icon = target_dir / "app.ico"
                except OSError:
                    icon = None
            else:
                icon = None

            self._set(step="criando atalhos...", percent=82)
            links, names = [], []
            if desktop:
                links.append(Path(os.path.expanduser("~")) / "Desktop" / f"{APP_NAME}.lnk")
                names.append("area de trabalho")
            if start_menu:
                appdata = os.environ.get("APPDATA")
                if appdata:
                    links.append(Path(appdata) / "Microsoft" / "Windows" /
                                 "Start Menu" / "Programs" / f"{APP_NAME}.lnk")
                    names.append("menu iniciar")
            made = _make_shortcuts(target, links, icon)

            self._set(step="registrando...", percent=93)
            write_uninstaller(target_dir)
            try:
                register_uninstall(target, int(target.stat().st_size / 1024))
            except OSError:
                pass

            if launch:
                self._set(step="abrindo o AptPlayer...", percent=98)
                try:
                    subprocess.Popen([str(target)], cwd=str(target_dir))
                except OSError:
                    pass

            self._set(running=False, done=True, ok=True, percent=100,
                      step="pronto", shortcuts=names[:made] if made else [])
        except Exception as exc:              # nunca deixa a thread morrer calada
            self._set(running=False, done=True, ok=False, error=str(exc))

    def _copy_with_progress(self, source: Path, target: Path) -> None:
        """Copia em blocos para poder reportar andamento (15% -> 80%)."""
        total = source.stat().st_size or 1
        copied = 0
        with open(source, "rb") as src, open(target, "wb") as dst:
            while True:
                chunk = src.read(1024 * 1024)
                if not chunk:
                    break
                dst.write(chunk)
                copied += len(chunk)
                self._set(percent=15 + int(copied / total * 65))
        shutil.copystat(source, target)

    def close(self) -> dict:
        if _window:
            _window.destroy()
        return {"ok": True}


HTML = """<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body {
  font-family: "Segoe UI", system-ui, sans-serif;
  background: #05060a; color: #e8ecf8; height: 100vh;
  display: flex; flex-direction: column; user-select: none; overflow: hidden;
}
body::before {
  content:''; position:fixed; inset:0; pointer-events:none;
  background:
    radial-gradient(ellipse 70% 50% at 50% 0%, rgba(0,240,255,.10), transparent 60%),
    radial-gradient(ellipse 60% 50% at 100% 100%, rgba(252,238,10,.06), transparent 60%);
}
.wrap { position:relative; flex:1; display:flex; flex-direction:column;
        align-items:center; justify-content:center; padding:34px; text-align:center; }
.logo { width:104px; height:104px; margin-bottom:20px;
        filter: drop-shadow(0 0 22px rgba(252,238,10,.45)); }
h1 { font-size:27px; font-weight:700; letter-spacing:2px; text-transform:uppercase; }
h1 span { color:#fcee0a; }
.ver { font-family:Consolas,monospace; font-size:12px; color:#00f0ff;
       letter-spacing:2px; margin:9px 0 22px; }
.path { font-family:Consolas,monospace; font-size:11px; color:#5a6683;
        background:#0e1220; border:1px solid rgba(0,240,255,.14);
        padding:9px 14px; margin-bottom:22px; max-width:100%;
        overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.opts { display:flex; flex-direction:column; gap:10px; margin-bottom:26px; }
label { display:flex; align-items:center; gap:9px; font-size:13.5px;
        color:#8b97b4; cursor:pointer; }
label:hover { color:#e8ecf8; }
input[type=checkbox] { width:16px; height:16px; accent-color:#fcee0a; cursor:pointer; }
.btn { background:#fcee0a; color:#05060a; border:none;
       padding:15px 46px; font:inherit; font-size:14px; font-weight:700;
       letter-spacing:1.4px; text-transform:uppercase; cursor:pointer;
       clip-path: polygon(0 0,100% 0,100% 68%,calc(100% - 12px) 100%,0 100%);
       box-shadow:0 0 18px rgba(252,238,10,.45); transition:all .15s; }
.btn:hover { background:#fff45a; box-shadow:0 0 26px rgba(252,238,10,.8); }
.btn:disabled { opacity:.45; cursor:default; box-shadow:none; }
.msg { margin-top:18px; font-size:13px; min-height:20px; color:#8b97b4; }
.bar { width:100%; max-width:330px; height:5px; background:#131828;
       border:1px solid rgba(0,240,255,.14); margin-top:16px;
       opacity:0; transition:opacity .2s; }
.bar.on { opacity:1; }
.bar-fill { height:100%; width:0; background:linear-gradient(90deg,#00f0ff,#fcee0a);
            transition:width .25s ease; }
.msg.ok { color:#fcee0a; }
.msg.err { color:#ff2a6d; }
.foot { padding:13px; font-size:10.5px; color:#4a5675; font-family:Consolas,monospace;
        border-top:1px solid rgba(0,240,255,.1); position:relative; }
</style></head><body>
<div class="wrap">
  <img src="app.png" class="logo" alt="" onerror="this.style.display='none'">
  <h1>Apt<span>Player</span></h1>
  <div class="ver" id="ver">v—</div>
  <div class="path" id="path">—</div>
  <div class="opts">
    <label><input type="checkbox" id="desk" checked> Atalho na área de trabalho</label>
    <label><input type="checkbox" id="menu" checked> Atalho no menu iniciar</label>
    <label><input type="checkbox" id="run" checked> Abrir depois de instalar</label>
  </div>
  <button class="btn" id="go">Instalar</button>
  <div class="bar" id="bar"><div class="bar-fill" id="fill"></div></div>
  <div class="msg" id="msg"></div>
</div>
<div class="foot">Instala para o usuário atual · não precisa de administrador</div>
<script>
const $ = (id) => document.getElementById(id);
window.addEventListener('pywebviewready', async () => {
  const info = await window.pywebview.api.get_info();
  $('ver').textContent = 'v' + info.version;
  $('path').textContent = info.path;
  if (info.installed) {
    $('go').textContent = 'Atualizar';
    $('msg').textContent = 'Uma versão já está instalada.';
  }
});
$('go').addEventListener('click', async () => {
  const btn = $('go'), msg = $('msg'), bar = $('bar'), fill = $('fill');
  btn.disabled = true; btn.textContent = 'Instalando...';
  msg.className = 'msg'; msg.textContent = 'preparando...';
  bar.classList.add('on');

  // Dispara e volta na hora: o trabalho roda em outra thread no Python,
  // senao a janela congelaria durante a copia.
  await window.pywebview.api.install(
    $('desk').checked, $('menu').checked, $('run').checked);

  const poll = setInterval(async () => {
    const p = await window.pywebview.api.progress();
    fill.style.width = (p.percent || 0) + '%';
    if (p.step) msg.textContent = p.step;

    if (!p.done) return;
    clearInterval(poll);

    if (!p.ok) {
      btn.disabled = false; btn.textContent = 'Tentar de novo';
      bar.classList.remove('on');
      msg.className = 'msg err';
      msg.textContent = p.error || 'falhou';
      return;
    }
    btn.textContent = 'Pronto';
    msg.className = 'msg ok';
    msg.textContent = 'Instalado' + (p.shortcuts && p.shortcuts.length
      ? ' - atalho em ' + p.shortcuts.join(' e ') : '');
    setTimeout(() => window.pywebview.api.close(), 2000);
  }, 200);
});
</script></body></html>
"""


def main():
    _trace("main inicio")
    tmp = Path(os.environ.get("TEMP", ".")) / "aptplayer_installer.html"
    tmp.write_text(HTML, encoding="utf-8")

    # o logo fica ao lado do html para o <img> encontrar
    logo = resource("app.png")
    if logo.exists():
        try:
            shutil.copy2(logo, tmp.parent / "app.png")
        except OSError:
            pass

    _trace("html escrito")
    global _window
    api = InstallerApi()
    _trace("api criada")
    window = webview.create_window(
        f"Instalar {APP_NAME}", str(tmp), js_api=api,
        width=520, height=640, resizable=False, background_color="#05060a",
    )
    _window = window
    _trace("janela criada")
    icon = resource("app.ico")
    kwargs = {"icon": str(icon)} if icon.exists() else {}
    _trace(f"iniciando webview kwargs={list(kwargs)}")
    try:
        webview.start(**kwargs)
    except TypeError:
        _trace("TypeError no start; tentando sem icon")
        webview.start()
    _trace("webview terminou")


if __name__ == "__main__":
    main()
