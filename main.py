"""AptPlayer - player de musica com YouTube, cache local e IA via Ollama."""

import mimetypes
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import webview

from core import cache, library
from core.api import Api
from core.paths import ensure_dirs, resource_dir

ROOT = resource_dir()
UI_DIR = ROOT / "ui"
ICON = ROOT / "icon" / "app.ico"


class _MediaHandler(BaseHTTPRequestHandler):
    """Serve os arquivos em cache com suporte a Range (seek na barra)."""

    def log_message(self, *args):
        pass  # silencia o log padrao do http.server

    def _send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")

    def do_GET(self):
        if self.path.startswith("/cover/"):
            self._serve_cover()
            return
        if not self.path.startswith("/local/"):
            self.send_error(404)
            return

        video_id = self.path[len("/local/"):].split("?")[0]
        path = cache.cached_file(video_id)
        if not path:
            self.send_error(404)
            return

        file_path = Path(path)
        size = file_path.stat().st_size
        ctype = mimetypes.guess_type(str(file_path))[0] or "audio/mp4"

        start, end = 0, size - 1
        range_header = self.headers.get("Range")
        if range_header and range_header.startswith("bytes="):
            raw = range_header[6:].split("-")
            try:
                if raw[0]:
                    start = int(raw[0])
                if len(raw) > 1 and raw[1]:
                    end = int(raw[1])
            except ValueError:
                start, end = 0, size - 1
            start = max(0, min(start, size - 1))
            end = max(start, min(end, size - 1))
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        else:
            self.send_response(200)

        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        self._send_cors()
        self.end_headers()

        with open(file_path, "rb") as fh:
            fh.seek(start)
            remaining = end - start + 1
            while remaining > 0:
                chunk = fh.read(min(64 * 1024, remaining))
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionAbortedError):
                    break  # o player pulou de faixa; normal
                remaining -= len(chunk)


    def _serve_cover(self):
        """Serve a capa de uma playlist (data/covers)."""
        raw = self.path[len("/cover/"):].split("?")[0]
        try:
            playlist_id = int(raw)
        except ValueError:
            self.send_error(404)
            return

        playlist = library.get_playlist(playlist_id)
        cover = (playlist or {}).get("cover")
        if not cover or not Path(cover).exists():
            self.send_error(404)
            return

        data = Path(cover).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(cover)[0] or "image/jpeg")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self._send_cors()
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionAbortedError):
            pass


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start_media_server() -> int:
    port = _free_port()
    server = HTTPServer(("127.0.0.1", port), _MediaHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return port


def _set_taskbar_identity():
    """Sem isto o Windows agrupa a janela sob o icone do python.exe."""
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "AptPlayer.Music.Player.1"
        )
    except Exception:
        pass


def main():
    _set_taskbar_identity()
    ensure_dirs()

    # remove o executavel antigo deixado por uma atualizacao anterior
    try:
        from core import autoupdate
        autoupdate.cleanup_old()
    except Exception:
        pass

    library.init_db()
    port = start_media_server()

    api = Api()
    window = webview.create_window(
        "AptPlayer",
        str(UI_DIR / "index.html"),
        js_api=api,
        width=1280,
        height=820,
        min_size=(940, 620),
        background_color="#05060a",
    )

    def on_start():
        # Informa a porta do servidor de midia para a interface.
        window.evaluate_js(f"window.MEDIA_PORT = {port};")

    kwargs = {"debug": False}
    if ICON.exists():
        kwargs["icon"] = str(ICON)
    try:
        webview.start(on_start, **kwargs)
    except TypeError:
        # Versoes antigas do pywebview nao aceitam icon=
        webview.start(on_start, debug=False)


if __name__ == "__main__":
    main()
