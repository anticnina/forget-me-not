import configparser
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path

_conn = None


def _load_cfg():
    cfg = configparser.ConfigParser()
    cfg.read(Path(__file__).parent.parent / "config.ini")
    return cfg["database"]


def get_connection():
    global _conn
    if _conn is None or _conn.closed:
        db = _load_cfg()
        _conn = psycopg2.connect(
            host=db["host"],
            port=int(db["port"]),
            dbname=db["dbname"],
            user=db["user"],
            password=db["password"],
        )
        _conn.autocommit = True
    return _conn


def execute(sql: str, params=None, fetch: str | None = None):
    """
    Run *sql* with optional *params*.

    fetch='one'  → returns first row as dict (or None)
    fetch='all'  → returns list of dicts
    fetch=None   → returns rowcount (for INSERT/UPDATE/DELETE without RETURNING)
    """
    conn = get_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params)
        if fetch == "one":
            row = cur.fetchone()
            return dict(row) if row else None
        if fetch == "all":
            rows = cur.fetchall()
            return [dict(r) for r in rows] if rows else []
        return cur.rowcount
