"""Ponte entre a interface (JS) e o backend (Python).

Cada metodo publico desta classe fica disponivel no JS como
window.pywebview.api.<nome>(...).
"""

from pathlib import Path

from . import (account, ai, autoupdate, cache, discover, hotkeys, library,
               lyrics,
               radio, share, spotify, stats, translate, updater, youtube)
from .paths import COVERS_DIR


class Api:
    def __init__(self):
        library.init_db()
        # Importacao do Spotify roda em thread; a interface acompanha o estado.
        import threading
        self._import_lock = threading.Lock()
        self._import = {
            "running": False, "done": False, "ok": False,
            "step": "", "found": 0, "total": 0,
            "error": "", "playlist_id": 0, "name": "",
        }

    # --- busca ------------------------------------------------------------

    def search(self, query: str, limit: int = 20) -> dict:
        try:
            return {"ok": True, "results": youtube.search(query, limit)}
        except Exception as exc:
            if not self._online():
                return {"ok": False, "offline": True,
                        "error": "Sem internet. Suas musicas em cache ainda tocam."}
            return {"ok": False, "error": f"Falha na busca: {exc}"}

    @staticmethod
    def _online(timeout: float = 3.0) -> bool:
        """Testa conectividade real (nao so a placa de rede)."""
        import socket
        for host in ("www.youtube.com", "1.1.1.1"):
            try:
                socket.create_connection((host, 443), timeout=timeout).close()
                return True
            except OSError:
                continue
        return False

    def resolve_stream(self, video_id: str) -> dict:
        """Devolve arquivo local se houver cache, senao a URL de stream."""
        local = cache.cached_file(video_id)
        if local:
            return {"ok": True, "source": "cache", "url": f"/local/{video_id}"}

        url = youtube.get_stream_url(video_id)
        if not url:
            if not self._online():
                return {"ok": False, "offline": True,
                        "error": "Sem internet. So tocam as faixas baixadas."}
            return {
                "ok": False,
                "error": "Nao consegui resolver o audio. Tente 'pip install -U yt-dlp'.",
            }
        return {"ok": True, "source": "stream", "url": url}

    def prefetch(self, video_id: str) -> dict:
        youtube.prefetch_stream(video_id)
        return {"ok": True}

    # --- reproducao -------------------------------------------------------

    def play_started(self, track: dict) -> dict:
        """Chamado quando uma faixa comeca: registra e avalia o cache."""
        library.add_track(track)
        library.record_play(track["video_id"])
        cache.maybe_cache(track["video_id"])
        return {"ok": True}

    # --- biblioteca -------------------------------------------------------

    def get_library(self, order: str = "recent") -> dict:
        return {"ok": True, "tracks": library.all_tracks(order)}

    def get_favorites(self) -> dict:
        return {"ok": True, "tracks": library.favorites()}

    def get_history(self, limit: int = 50) -> dict:
        return {"ok": True, "tracks": library.history(limit)}

    def get_top_played(self, limit: int = 30) -> dict:
        return {"ok": True, "tracks": library.top_played(limit)}

    def add_track(self, track: dict) -> dict:
        library.add_track(track)
        return {"ok": True}

    def toggle_favorite(self, video_id: str) -> dict:
        return {"ok": True, "favorite": library.toggle_favorite(video_id)}

    def delete_track(self, video_id: str) -> dict:
        cache.remove_cached(video_id)
        library.delete_track(video_id)
        return {"ok": True}

    # --- playlists --------------------------------------------------------

    def get_playlists(self) -> dict:
        return {"ok": True, "playlists": library.all_playlists()}

    def get_playlist(self, playlist_id: int) -> dict:
        return {
            "ok": True,
            "tracks": library.playlist_tracks(int(playlist_id)),
            "playlist": library.get_playlist(int(playlist_id)),
        }

    def rename_playlist(self, playlist_id: int, name: str) -> dict:
        name = (name or "").strip()
        if not name:
            return {"ok": False, "error": "Nome vazio."}
        library.rename_playlist(int(playlist_id), name)
        return {"ok": True}

    def pick_playlist_cover(self, playlist_id: int) -> dict:
        """Abre o seletor de arquivo e copia a imagem para data/covers."""
        import shutil
        import time as _time

        import webview

        windows = webview.windows
        if not windows:
            return {"ok": False, "error": "Janela indisponivel."}

        chosen = windows[0].create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=("Imagens (*.png;*.jpg;*.jpeg;*.gif;*.webp)",),
        )
        if not chosen:
            return {"ok": False, "cancelled": True}

        src = Path(chosen[0])
        if not src.exists():
            return {"ok": False, "error": "Arquivo nao encontrado."}

        COVERS_DIR.mkdir(parents=True, exist_ok=True)
        dest = COVERS_DIR / f"pl{int(playlist_id)}_{int(_time.time())}{src.suffix.lower()}"
        try:
            shutil.copy2(src, dest)
        except OSError as exc:
            return {"ok": False, "error": f"Falha ao copiar: {exc}"}

        library.set_playlist_cover(int(playlist_id), str(dest))
        return {"ok": True, "cover": f"/cover/{int(playlist_id)}?v={int(_time.time())}"}

    def remove_playlist_cover(self, playlist_id: int) -> dict:
        library.set_playlist_cover(int(playlist_id), None)
        return {"ok": True}

    def create_playlist(self, name: str) -> dict:
        name = (name or "").strip()
        if not name:
            return {"ok": False, "error": "Nome vazio."}
        return {"ok": True, "id": library.create_playlist(name)}

    def add_to_playlist(self, playlist_id: int, video_id: str) -> dict:
        library.add_to_playlist(int(playlist_id), video_id)
        return {"ok": True}

    def remove_from_playlist(self, playlist_id: int, video_id: str) -> dict:
        library.remove_from_playlist(int(playlist_id), video_id)
        return {"ok": True}

    def delete_playlist(self, playlist_id: int) -> dict:
        library.delete_playlist(int(playlist_id))
        return {"ok": True}

    # --- cache ------------------------------------------------------------

    def cache_stats(self) -> dict:
        return {"ok": True, "stats": cache.cache_stats()}

    def force_cache(self, video_id: str) -> dict:
        return {"ok": True, "state": cache.force_cache(video_id)}

    def cache_status(self, video_ids: list) -> dict:
        return {"ok": True, "states": cache.status_many(list(video_ids or []))}

    def cache_playlist(self, playlist_id: int) -> dict:
        """Baixa a playlist inteira para ouvir offline."""
        tracks = library.playlist_tracks(int(playlist_id))
        if not tracks:
            return {"ok": False, "error": "Playlist vazia."}
        result = cache.cache_many([t["video_id"] for t in tracks])
        return {"ok": True, **result}

    def cache_tracks(self, video_ids: list) -> dict:
        """Baixa varias faixas (usado por 'baixar tudo' em listas)."""
        ids = list(video_ids or [])
        if not ids:
            return {"ok": False, "error": "Nenhuma faixa."}
        return {"ok": True, **cache.cache_many(ids)}

    def remove_cached(self, video_id: str) -> dict:
        cache.remove_cached(video_id)
        return {"ok": True}

    # --- IA ---------------------------------------------------------------

    def ai_status(self) -> dict:
        available = ai.is_available()
        models = ai.list_models() if available else []
        return {
            "ok": True,
            "available": available,
            "models": models,
            "active": ai.pick_model() if models else None,
        }

    def ai_set_model(self, name: str) -> dict:
        ai.set_model(name)
        return {"ok": True}

    def ai_search(self, request: str) -> dict:
        """Pedido em linguagem natural -> faixas reais do YouTube."""
        if not ai.pick_model():
            return {"ok": False, "error": "Nenhum modelo do Ollama disponivel."}

        queries = ai.queries_from_request(request)
        if not queries:
            return {"ok": False, "error": "A IA nao devolveu sugestoes utilizaveis."}

        results, seen = [], set()
        for query in queries:
            try:
                found = youtube.search(query, limit=1)
            except Exception:
                continue
            for track in found:
                if track["video_id"] not in seen:
                    seen.add(track["video_id"])
                    results.append(track)

        if not results:
            return {"ok": False, "error": "Nao achei nada no YouTube para as sugestoes."}
        return {"ok": True, "results": results, "queries": queries}

    def ai_playlist(self, description: str, name: str = "") -> dict:
        """Monta uma playlist a partir da biblioteca e salva."""
        if not ai.pick_model():
            return {"ok": False, "error": "Nenhum modelo do Ollama disponivel."}

        video_ids = ai.playlist_from_library(description)
        if not video_ids:
            return {
                "ok": False,
                "error": "A IA nao escolheu faixas. Sua biblioteca pode estar pequena demais.",
            }

        playlist_name = (name or "").strip() or f"IA: {description[:40]}"
        playlist_id = library.create_playlist(playlist_name)
        for video_id in video_ids:
            library.add_to_playlist(playlist_id, video_id)

        return {
            "ok": True,
            "id": playlist_id,
            "name": playlist_name,
            "count": len(video_ids),
        }

    def ai_tag_library(self, limit: int = 20) -> dict:
        if not ai.pick_model():
            return {"ok": False, "error": "Nenhum modelo do Ollama disponivel."}
        updated = ai.tag_tracks(int(limit))
        return {"ok": True, "updated": updated}

    # --- chat com a IA ----------------------------------------------------

    def ai_chat(self, messages: list) -> dict:
        """Conversa livre. Devolve o texto e as faixas que a IA mandou tocar."""
        if not ai.pick_model():
            return {"ok": False, "error": "Nenhum modelo do Ollama disponivel."}

        clean = [
            {"role": m.get("role", "user"), "content": str(m.get("content", ""))}
            for m in (messages or [])
            if m.get("content")
        ][-12:]  # mantem a janela de contexto curta
        if not clean:
            return {"ok": False, "error": "Mensagem vazia."}

        reply = ai.chat(clean)
        if reply is None:
            return {"ok": False, "error": "A IA nao respondeu. O Ollama esta rodando?"}

        suggestions = []
        for query in ai.extract_play_requests(reply):
            try:
                found = youtube.search(query, limit=1)
            except Exception:
                continue
            if found:
                suggestions.append(found[0])

        return {
            "ok": True,
            "reply": ai.strip_play_lines(reply) or reply,
            "suggestions": suggestions,
        }

    # --- radio -----------------------------------------------------------

    def radio_start(self, seed: dict, count: int = 12, use_ai: bool = True) -> dict:
        """Inicia um radio a partir de uma faixa: fila de musicas parecidas."""
        if not seed or not seed.get("video_id"):
            return {"ok": False, "error": "Faixa invalida."}

        radio.reset(seed["video_id"])
        try:
            tracks = radio.build(seed, count, use_ai=bool(use_ai))
        except Exception as exc:
            return {"ok": False, "error": f"Falha no radio: {exc}"}

        if not tracks:
            return {"ok": False, "error": "Nao encontrei musicas parecidas."}
        return {"ok": True, "tracks": tracks}

    def radio_more(self, seed: dict, count: int = 10, use_ai: bool = True) -> dict:
        """Mais faixas para o radio em andamento (fila infinita)."""
        if not seed or not seed.get("video_id"):
            return {"ok": False, "error": "Faixa invalida."}
        try:
            tracks = radio.build(seed, count, use_ai=bool(use_ai))
        except Exception as exc:
            return {"ok": False, "error": f"Falha no radio: {exc}"}
        return {"ok": True, "tracks": tracks}

    # --- ajustes ----------------------------------------------------------

    def open_data_folder(self) -> dict:
        """Abre a pasta de dados no Explorer."""
        import subprocess

        from .paths import DATA_DIR

        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            subprocess.Popen(["explorer", str(DATA_DIR)])
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    # --- descobrir --------------------------------------------------------

    def discover_home(self, limit: int = 18) -> dict:
        """Secoes da tela inicial."""
        try:
            return {"ok": True, "sections": discover.home(int(limit))}
        except Exception as exc:
            return {"ok": False, "error": f"Falha ao montar a home: {exc}"}

    def discover_categories(self) -> dict:
        return {"ok": True, **discover.categories()}

    def discover_category(self, category_id: str, limit: int = 24) -> dict:
        tracks = discover.category_tracks(category_id, int(limit))
        if not tracks:
            return {"ok": False, "error": "Nada encontrado nesta categoria."}
        return {"ok": True, "tracks": tracks}

    # --- letras -----------------------------------------------------------

    def get_lyrics(self, artist: str, title: str, duration: int = 0) -> dict:
        """Letra da faixa, sincronizada quando existir."""
        try:
            data = lyrics.fetch(artist, title, int(duration or 0))
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
        if not data:
            return {"ok": False, "error": "Letra nao encontrada para esta faixa."}
        return {"ok": True, **data}

    # --- atualizacao e diagnostico ----------------------------------------

    def app_version(self) -> dict:
        return {"ok": True, "version": updater.VERSION}

    def check_update(self) -> dict:
        result = updater.check()
        if result.get("update") and updater.is_snoozed(result["latest"]):
            result["update"] = False
        return result

    def snooze_update(self, version: str) -> dict:
        updater.snooze(version)
        return {"ok": True}

    def diagnostics(self) -> dict:
        """Estado geral, para a tela de ajustes."""
        import sys

        from . import paths

        return {
            "ok": True,
            "version": updater.VERSION,
            "online": self._online(),
            "ollama": ai.is_available(),
            "model": ai.pick_model(),
            "python": sys.version.split()[0],
            "data_dir": str(paths.DATA_DIR),
            "frozen": paths.FROZEN,
            "cache": cache.cache_stats(),
            "tracks": len(library.all_tracks()),
            "playlists": len(library.all_playlists()),
        }

    # --- importar do Spotify ---------------------------------------------

    def spotify_preview(self, url: str) -> dict:
        """Le a playlist sem importar, para o usuario confirmar."""
        result = spotify.fetch_tracks(url)
        if not result.get("ok"):
            return result
        return {
            "ok": True,
            "name": result["name"],
            "kind": result["kind"],
            "count": len(result["items"]),
            "sample": result["items"][:5],
        }

    def spotify_import(self, url: str, name: str = "", limit: int = 0) -> dict:
        """Importa em background: cada faixa vira uma busca no YouTube."""
        import threading

        with self._import_lock:
            if self._import["running"]:
                return {"ok": True, "started": False}
            self._import = {
                "running": True, "done": False, "ok": False,
                "step": "lendo a playlist...", "found": 0, "total": 0,
                "error": "", "playlist_id": 0, "name": "",
            }

        threading.Thread(
            target=self._run_spotify_import,
            args=(url, name, int(limit or 0)),
            daemon=True,
        ).start()
        return {"ok": True, "started": True}

    def spotify_progress(self) -> dict:
        with self._import_lock:
            return dict(self._import)

    def _set_import(self, **kw) -> None:
        with self._import_lock:
            self._import.update(kw)

    def _run_spotify_import(self, url: str, name: str, limit: int) -> None:
        try:
            data = spotify.fetch_tracks(url)
            if not data.get("ok"):
                self._set_import(running=False, done=True, ok=False,
                                 error=data.get("error", "falha ao ler"))
                return

            items = data["items"][:limit] if limit else data["items"]
            playlist_name = (name or "").strip() or data["name"]
            self._set_import(total=len(items), name=playlist_name,
                             step="procurando as faixas no YouTube...")

            playlist_id = library.create_playlist(playlist_name)
            found = 0

            for index, item in enumerate(items, 1):
                query = f"{item['artist']} {item['title']}".strip()
                self._set_import(step=f"{index}/{len(items)}: {query[:48]}")
                try:
                    results = youtube.search(query, limit=1)
                except Exception:
                    results = []
                if results:
                    track = results[0]
                    library.add_track(track)
                    library.add_to_playlist(playlist_id, track["video_id"])
                    found += 1
                    self._set_import(found=found)

            self._set_import(running=False, done=True, ok=True,
                             playlist_id=playlist_id, step="pronto")
        except Exception as exc:
            self._set_import(running=False, done=True, ok=False, error=str(exc))

    def spotify_cancel(self) -> dict:
        self._set_import(running=False, done=True, ok=False, error="cancelado")
        return {"ok": True}

    # --- conta e sincronizacao --------------------------------------------

    def account_status(self) -> dict:
        return {
            "ok": True,
            "configured": account.is_configured(),
            "user": account.current_user(),
        }

    def account_signup(self, email: str, password: str) -> dict:
        email = (email or "").strip()
        if "@" not in email or len(password or "") < 6:
            return {"ok": False, "error": "Email invalido ou senha com menos de 6 caracteres."}
        return account.sign_up(email, password)

    def account_login(self, email: str, password: str) -> dict:
        return account.sign_in((email or "").strip(), password or "")

    def account_logout(self) -> dict:
        account.logout()
        return {"ok": True}

    def account_upload(self) -> dict:
        """Envia a biblioteca para a nuvem."""
        snapshot = library.export_snapshot()
        result = account.upload(snapshot)
        if result.get("ok"):
            result["playlists"] = len(snapshot.get("playlists", []))
        return result

    def account_download(self, replace: bool = False) -> dict:
        """Traz a biblioteca da nuvem para este PC."""
        result = account.download()
        if not result.get("ok"):
            return result
        restored = library.import_snapshot(result["data"], replace=bool(replace))
        if not restored.get("ok"):
            return restored
        return {"ok": True, "updated_at": result.get("updated_at", ""), **restored}

    # --- backup em arquivo (funciona sem conta) ---------------------------

    def export_backup(self) -> dict:
        """Salva a biblioteca num arquivo escolhido pelo usuario."""
        import json

        import webview

        windows = webview.windows
        if not windows:
            return {"ok": False, "error": "Janela indisponivel."}

        chosen = windows[0].create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename="aptplayer-backup.json",
            file_types=("JSON (*.json)",),
        )
        if not chosen:
            return {"ok": False, "cancelled": True}

        path = Path(chosen if isinstance(chosen, str) else chosen[0])
        snapshot = library.export_snapshot()
        try:
            path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=1),
                            encoding="utf-8")
        except OSError as exc:
            return {"ok": False, "error": str(exc)}
        return {"ok": True, "path": str(path),
                "tracks": len(snapshot["tracks"]),
                "playlists": len(snapshot["playlists"])}

    def import_backup(self, replace: bool = False) -> dict:
        import json

        import webview

        windows = webview.windows
        if not windows:
            return {"ok": False, "error": "Janela indisponivel."}

        chosen = windows[0].create_file_dialog(
            webview.OPEN_DIALOG, allow_multiple=False,
            file_types=("JSON (*.json)",),
        )
        if not chosen:
            return {"ok": False, "cancelled": True}

        try:
            snapshot = json.loads(Path(chosen[0]).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            return {"ok": False, "error": f"Arquivo ilegivel: {exc}"}
        return library.import_snapshot(snapshot, replace=bool(replace))

    # --- estatisticas -----------------------------------------------------

    def get_stats(self, days: int = 0) -> dict:
        """Retrospectiva: days=0 e desde sempre, 7/30/365 recortam o periodo."""
        try:
            data = stats.summary(int(days or 0))
            data["by_hour"] = stats.by_hour(30)
            data["by_day"] = stats.by_day(30)
            data["streak"] = stats.streak()
            data["first"] = stats.first_play()
            return {"ok": True, **data}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    # --- teclas de midia globais ------------------------------------------

    def hotkeys_start(self) -> dict:
        """Liga as teclas de midia do teclado, mesmo com o app minimizado."""
        def on_key(action):
            window = self._window()
            if not window:
                return
            js = {
                "playpause": "document.getElementById('btn-play').click()",
                "next": "playNext(false)",
                "prev": "playPrev()",
                "stop": "audio.pause(); audio.currentTime = 0",
            }.get(action)
            if js:
                try:
                    window.evaluate_js(js)
                except Exception:
                    pass

        ok = hotkeys.start(on_key)
        return {"ok": True, "active": ok}

    def hotkeys_stop(self) -> dict:
        hotkeys.stop()
        return {"ok": True, "active": False}

    def hotkeys_status(self) -> dict:
        return {"ok": True, "active": hotkeys.is_active()}

    @staticmethod
    def _window():
        import webview
        return webview.windows[0] if webview.windows else None

    def minimize(self) -> dict:
        window = self._window()
        if window:
            window.minimize()
        return {"ok": True}

    # --- compartilhar playlist --------------------------------------------

    def share_playlist(self, playlist_id: int) -> dict:
        """Gera o codigo que outra pessoa cola no AptPlayer dela."""
        return share.export_playlist(int(playlist_id))

    def preview_shared(self, code: str) -> dict:
        """Mostra o que tem no codigo antes de importar."""
        parsed = share.parse_code(code)
        if not parsed.get("ok"):
            return parsed
        return {
            "ok": True,
            "name": parsed["name"],
            "count": parsed["count"],
            "sample": parsed["items"][:5],
        }

    def import_shared(self, code: str, name: str = "") -> dict:
        return share.import_code(code, name)

    # --- traducao ---------------------------------------------------------

    def translate_languages(self) -> dict:
        """Idiomas disponiveis para traduzir letras."""
        return {"ok": True, "languages": translate.languages()}

    def translate_text(self, text: str, target: str) -> dict:
        """Traduz um texto (a letra) para o idioma escolhido."""
        try:
            return translate.translate(text, target)
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def translate_lyrics(self, artist: str, title: str, duration: int,
                         target: str) -> dict:
        """Busca a letra e ja devolve traduzida, linha a linha quando da."""
        found = lyrics.fetch(artist, title, int(duration or 0))
        if not found:
            return {"ok": False, "error": "Letra nao encontrada."}

        if found["synced"] and found["lines"]:
            source = chr(10).join(line["line"] for line in found["lines"])
        else:
            source = found["plain"]

        result = translate.translate(source, target)
        if not result.get("ok"):
            return result

        translated = result["text"].splitlines()

        # letra sincronizada: casa cada linha traduzida com seu tempo
        if found["synced"] and found["lines"]:
            lines = []
            for index, line in enumerate(found["lines"]):
                lines.append({
                    "time": line["time"],
                    "line": translated[index] if index < len(translated) else "",
                })
            return {"ok": True, "synced": True, "lines": lines,
                    "engine": result.get("engine", "")}

        return {"ok": True, "synced": False, "plain": result["text"],
                "engine": result.get("engine", "")}

    # --- atualizacao automatica -------------------------------------------

    def can_auto_update(self) -> dict:
        return {"ok": True, "supported": autoupdate.can_auto_update()}

    def start_auto_update(self, url: str, version: str) -> dict:
        """Baixa e instala a versao nova, reiniciando o app no fim."""
        return autoupdate.start(url, version)

    def auto_update_progress(self) -> dict:
        return {"ok": True, **autoupdate.state()}
