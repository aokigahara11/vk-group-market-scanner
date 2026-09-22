import sqlite3
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_DIR = PROJECT_ROOT / "data" / "database"
USERS_DB_PATH = DB_DIR / "database.db"

conn: Optional[sqlite3.Connection] = None


def init_db():
    """Создает папку и инициализирует основное соединение."""
    global conn
    DB_DIR.mkdir(parents=True, exist_ok=True)

    database_conn = sqlite3.connect(USERS_DB_PATH, check_same_thread=False)
    database_conn.execute("PRAGMA foreign_keys = ON")
    conn = database_conn


def close_all_connections():
    """Закрывает все соединения."""
    if conn:
        conn.close()


init_db()