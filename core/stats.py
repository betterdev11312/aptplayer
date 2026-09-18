"""Estatisticas de escuta - a "Retrospectiva" do AptPlayer.

Tudo sai do historico local: nada e enviado para lugar nenhum. Como cada
reproducao vira uma linha em `history`, da para recortar por periodo.
"""

import time
from collections import Counter

from .library import _rows

DAY = 86400


def _since(days: int) -> int:
    return int(time.time()) - days * DAY


def summary(days: int = 0) -> dict:
    """Numeros gerais. days=0 significa desde sempre."""
    where = "WHERE h.played_at >= ?" if days else ""
    params = (_since(days),) if days else ()

    rows = _rows(
        f"""SELECT t.video_id, t.title, t.artist, t.duration, t.thumbnail,
                   t.genre, t.mood, COUNT(*) AS plays
            FROM history h
            JOIN tracks t ON t.video_id = h.video_id
            {where}
            GROUP BY t.video_id
            ORDER BY plays DESC""",
        params,
    )

    total_plays = sum(r["plays"] for r in rows)
    total_seconds = sum((r["duration"] or 0) * r["plays"] for r in rows)

    artists = Counter()
    genres = Counter()
    moods = Counter()
    for row in rows:
        artists[row["artist"] or "Desconhecido"] += row["plays"]
        if row["genre"]:
            genres[row["genre"]] += row["plays"]
        if row["mood"]:
            moods[row["mood"]] += row["plays"]

    return {
        "days": days,
        "total_plays": total_plays,
        "total_seconds": total_seconds,
        "unique_tracks": len(rows),
        "unique_artists": len(artists),
        "top_tracks": rows[:10],
        "top_artists": [
            {"name": name, "plays": plays} for name, plays in artists.most_common(10)
        ],
        "genres": [
            {"name": name, "plays": plays} for name, plays in genres.most_common(8)
        ],
        "moods": [
            {"name": name, "plays": plays} for name, plays in moods.most_common(6)
        ],
    }


def by_hour(days: int = 30) -> list[dict]:
    """Quantas faixas por hora do dia - mostra se voce e da madrugada."""
    rows = _rows(
        """SELECT CAST(strftime('%H', played_at, 'unixepoch', 'localtime') AS INTEGER) AS hour,
                  COUNT(*) AS plays
           FROM history
           WHERE played_at >= ?
           GROUP BY hour""",
        (_since(days),),
    )
    counts = {r["hour"]: r["plays"] for r in rows}
    return [{"hour": h, "plays": counts.get(h, 0)} for h in range(24)]


def by_day(days: int = 30) -> list[dict]:
    """Faixas por dia, para o grafico de atividade."""
    rows = _rows(
        """SELECT date(played_at, 'unixepoch', 'localtime') AS day,
                  COUNT(*) AS plays
           FROM history
           WHERE played_at >= ?
           GROUP BY day ORDER BY day""",
        (_since(days),),
    )
    return [{"day": r["day"], "plays": r["plays"]} for r in rows]


def streak() -> dict:
    """Dias seguidos ouvindo musica (atual e recorde)."""
    rows = _rows(
        """SELECT DISTINCT date(played_at, 'unixepoch', 'localtime') AS day
           FROM history ORDER BY day"""
    )
    days = [r["day"] for r in rows if r["day"]]
    if not days:
        return {"current": 0, "best": 0}

    from datetime import date, timedelta

    parsed = [date.fromisoformat(d) for d in days]
    best = current = 1
    for previous, day in zip(parsed, parsed[1:]):
        if day - previous == timedelta(days=1):
            current += 1
            best = max(best, current)
        else:
            current = 1

    today = date.today()
    # a sequencia atual so conta se termina hoje ou ontem
    if parsed[-1] not in (today, today - timedelta(days=1)):
        current = 0

    return {"current": current, "best": best}


def first_play() -> dict | None:
    """A primeira musica que voce tocou no app."""
    rows = _rows(
        """SELECT t.title, t.artist, h.played_at
           FROM history h JOIN tracks t ON t.video_id = h.video_id
           ORDER BY h.played_at ASC LIMIT 1"""
    )
    return rows[0] if rows else None
