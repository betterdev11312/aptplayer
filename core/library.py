"""Biblioteca local: faixas, playlists, favoritos e historico (SQLite)."""

import sqlite3
import time

from .paths import DB_PATH

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tracks (
    video_id       TEXT PRIMARY KEY,
    title          TEXT NOT NULL,
    artist         TEXT,
    duration       INTEGER DEFAULT 0,
    thumbnail      TEXT,
    genre          TEXT,
    mood           TEXT,
    favorite       INTEGER DEFAULT 0,
    play_count     INTEGER DEFAULT 0,
    cached_path    TEXT,
    added_at       INTEGER,
    last_played_at INTEGER
);

CREATE TABLE IF NOT EXISTS playlists (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    cover      TEXT,
    created_at INTEGER
);

CREATE TABLE IF NOT EXISTS playlist_tracks (
    playlist_id INTEGER NOT NULL,
    video_id    TEXT NOT NULL,
    position    INTEGER DEFAULT 0,
    PRIMARY KEY (playlist_id, video_id),
    FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
    FOREIGN KEY (video_id) REFERENCES tracks(video_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS history (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    played_at INTEGER
);

CREATE INDEX IF NOT EXISTS idx_tracks_favorite ON tracks(favorite);
CREATE INDEX IF NOT EXISTS idx_tracks_played ON tracks(last_played_at);
CREATE INDEX IF NOT EXISTS idx_history_time ON history(played_at);
"""


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(_SCHEMA)
        # Migracao para bancos criados antes da coluna de capa existir.
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(playlists)")}
        if "cover" not in cols:
            conn.execute("ALTER TABLE playlists ADD COLUMN cover TEXT")


def _rows(query: str, params: tuple = ()) -> list[dict]:
    with _connect() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]


# --- faixas ---------------------------------------------------------------

def add_track(track: dict) -> None:
    """Insere a faixa se ainda nao existir, preservando stats de quem ja existe."""
    with _connect() as conn:
        conn.execute(
            """INSERT INTO tracks (video_id, title, artist, duration, thumbnail, added_at)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(video_id) DO UPDATE SET
                   title = excluded.title,
                   artist = excluded.artist,
                   duration = excluded.duration,
                   thumbnail = excluded.thumbnail""",
            (
                track["video_id"],
                track.get("title", "Sem titulo"),
                track.get("artist", "Desconhecido"),
                track.get("duration", 0),
                track.get("thumbnail", ""),
                int(time.time()),
            ),
        )


def get_track(video_id: str) -> dict | None:
    found = _rows("SELECT * FROM tracks WHERE video_id = ?", (video_id,))
    return found[0] if found else None


def all_tracks(order: str = "recent") -> list[dict]:
    clause = {
        "recent": "ORDER BY added_at DESC",
        "played": "ORDER BY play_count DESC, last_played_at DESC",
        "title": "ORDER BY title COLLATE NOCASE ASC",
        "artist": "ORDER BY artist COLLATE NOCASE ASC, title COLLATE NOCASE ASC",
    }.get(order, "ORDER BY added_at DESC")
    return _rows(f"SELECT * FROM tracks {clause}")


def favorites() -> list[dict]:
    return _rows("SELECT * FROM tracks WHERE favorite = 1 ORDER BY added_at DESC")


def toggle_favorite(video_id: str) -> bool:
    with _connect() as conn:
        row = conn.execute(
            "SELECT favorite FROM tracks WHERE video_id = ?", (video_id,)
        ).fetchone()
        if row is None:
            return False
        new_value = 0 if row["favorite"] else 1
        conn.execute(
            "UPDATE tracks SET favorite = ? WHERE video_id = ?", (new_value, video_id)
        )
        return bool(new_value)


def delete_track(video_id: str) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM tracks WHERE video_id = ?", (video_id,))


def set_cached_path(video_id: str, path: str | None) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE tracks SET cached_path = ? WHERE video_id = ?", (path, video_id)
        )


def set_tags(video_id: str, genre: str | None, mood: str | None) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE tracks SET genre = ?, mood = ? WHERE video_id = ?",
            (genre, mood, video_id),
        )


def untagged_tracks(limit: int = 40) -> list[dict]:
    return _rows(
        """SELECT * FROM tracks
           WHERE genre IS NULL OR genre = ''
           ORDER BY play_count DESC LIMIT ?""",
        (limit,),
    )


# --- reproducao -----------------------------------------------------------

def record_play(video_id: str) -> None:
    now = int(time.time())
    with _connect() as conn:
        conn.execute(
            """UPDATE tracks
               SET play_count = play_count + 1, last_played_at = ?
               WHERE video_id = ?""",
            (now, video_id),
        )
        conn.execute(
            "INSERT INTO history (video_id, played_at) VALUES (?, ?)", (video_id, now)
        )


def history(limit: int = 50) -> list[dict]:
    return _rows(
        """SELECT t.*, MAX(h.played_at) AS played_at
           FROM history h JOIN tracks t ON t.video_id = h.video_id
           GROUP BY t.video_id
           ORDER BY played_at DESC LIMIT ?""",
        (limit,),
    )


def top_played(limit: int = 30) -> list[dict]:
    return _rows(
        """SELECT * FROM tracks WHERE play_count > 0
           ORDER BY play_count DESC LIMIT ?""",
        (limit,),
    )


# --- playlists ------------------------------------------------------------

def create_playlist(name: str) -> int:
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO playlists (name, created_at) VALUES (?, ?)",
            (name, int(time.time())),
        )
        return cur.lastrowid


def rename_playlist(playlist_id: int, name: str) -> None:
    with _connect() as conn:
        conn.execute("UPDATE playlists SET name = ? WHERE id = ?", (name, playlist_id))


def set_playlist_cover(playlist_id: int, cover: str | None) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE playlists SET cover = ? WHERE id = ?", (cover, playlist_id)
        )


def get_playlist(playlist_id: int) -> dict | None:
    found = _rows("SELECT * FROM playlists WHERE id = ?", (playlist_id,))
    return found[0] if found else None


def all_playlists() -> list[dict]:
    return _rows(
        """SELECT p.*, COUNT(pt.video_id) AS track_count
           FROM playlists p
           LEFT JOIN playlist_tracks pt ON pt.playlist_id = p.id
           GROUP BY p.id ORDER BY p.created_at DESC"""
    )


def playlist_tracks(playlist_id: int) -> list[dict]:
    return _rows(
        """SELECT t.* FROM playlist_tracks pt
           JOIN tracks t ON t.video_id = pt.video_id
           WHERE pt.playlist_id = ?
           ORDER BY pt.position ASC""",
        (playlist_id,),
    )


def add_to_playlist(playlist_id: int, video_id: str) -> None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT COALESCE(MAX(position), -1) + 1 AS next FROM playlist_tracks WHERE playlist_id = ?",
            (playlist_id,),
        ).fetchone()
        conn.execute(
            """INSERT OR IGNORE INTO playlist_tracks (playlist_id, video_id, position)
               VALUES (?, ?, ?)""",
            (playlist_id, video_id, row["next"]),
        )


def remove_from_playlist(playlist_id: int, video_id: str) -> None:
    with _connect() as conn:
        conn.execute(
            "DELETE FROM playlist_tracks WHERE playlist_id = ? AND video_id = ?",
            (playlist_id, video_id),
        )


def delete_playlist(playlist_id: int) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))


# --- backup / restauracao -------------------------------------------------

def export_snapshot() -> dict:
    """Empacota a biblioteca inteira num dict (para nuvem ou arquivo).

    Guarda so o que nao da para recriar: metadados, favoritas, contagens e
    playlists. Os audios em cache ficam de fora - sao baixados de novo.
    """
    tracks = all_tracks()
    playlists = []
    for playlist in all_playlists():
        playlists.append({
            "name": playlist["name"],
            "created_at": playlist.get("created_at"),
            "tracks": [t["video_id"] for t in playlist_tracks(playlist["id"])],
        })

    return {
        "version": 1,
        "exported_at": int(time.time()),
        "tracks": [
            {
                "video_id": t["video_id"],
                "title": t["title"],
                "artist": t["artist"],
                "duration": t.get("duration", 0),
                "thumbnail": t.get("thumbnail", ""),
                "genre": t.get("genre"),
                "mood": t.get("mood"),
                "favorite": t.get("favorite", 0),
                "play_count": t.get("play_count", 0),
            }
            for t in tracks
        ],
        "playlists": playlists,
    }


def import_snapshot(snapshot: dict, replace: bool = False) -> dict:
    """Restaura um snapshot. Sem replace, mescla com o que ja existe."""
    if not isinstance(snapshot, dict) or "tracks" not in snapshot:
        return {"ok": False, "error": "Backup invalido."}

    with _connect() as conn:
        if replace:
            conn.execute("DELETE FROM playlist_tracks")
            conn.execute("DELETE FROM playlists")
            conn.execute("DELETE FROM tracks")

    added = 0
    for track in snapshot.get("tracks", []):
        if not track.get("video_id"):
            continue
        add_track(track)
        # add_track nao mexe nestes campos, para nao perder o que ja existia
        with _connect() as conn:
            conn.execute(
                """UPDATE tracks
                   SET favorite = MAX(favorite, ?),
                       play_count = MAX(play_count, ?),
                       genre = COALESCE(genre, ?),
                       mood = COALESCE(mood, ?)
                   WHERE video_id = ?""",
                (int(track.get("favorite", 0)), int(track.get("play_count", 0)),
                 track.get("genre"), track.get("mood"), track["video_id"]),
            )
        added += 1

    existing = {p["name"] for p in all_playlists()}
    created = 0
    for playlist in snapshot.get("playlists", []):
        name = playlist.get("name")
        if not name or name in existing:
            continue
        playlist_id = create_playlist(name)
        for video_id in playlist.get("tracks", []):
            add_to_playlist(playlist_id, video_id)
        created += 1

    return {"ok": True, "tracks": added, "playlists": created}
