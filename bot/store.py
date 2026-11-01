"""Almacenamiento en SQLite: historial por cliente, leads y escalamientos."""
import json
import sqlite3
import time
from contextlib import contextmanager

from . import config


@contextmanager
def _conn():
    conn = sqlite3.connect(config.DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                phone TEXT PRIMARY KEY,
                messages TEXT NOT NULL,
                updated_at REAL NOT NULL,
                human_takeover REAL NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS processed_messages (
                wa_message_id TEXT PRIMARY KEY,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT NOT NULL,
                nombre TEXT,
                interes TEXT,
                detalles TEXT,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS escalations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT NOT NULL,
                motivo TEXT,
                resumen TEXT,
                created_at REAL NOT NULL
            );
            """
        )


def already_processed(wa_message_id: str) -> bool:
    """Marca el mensaje como procesado; devuelve True si ya lo estaba (WhatsApp reintenta)."""
    with _conn() as c:
        try:
            c.execute(
                "INSERT INTO processed_messages VALUES (?, ?)", (wa_message_id, time.time())
            )
            return False
        except sqlite3.IntegrityError:
            return True


def _takeover_active(ts: float) -> bool:
    """human_takeover guarda el momento en que una persona tomó el chat (0 = nadie)."""
    return bool(ts) and time.time() - ts < config.HUMAN_PAUSE_HOURS * 3600


def load_conversation(phone: str) -> tuple[list, bool]:
    """Devuelve (mensajes, human_takeover activo). Reinicia si la conversación expiró."""
    with _conn() as c:
        row = c.execute(
            "SELECT messages, updated_at, human_takeover FROM conversations WHERE phone = ?",
            (phone,),
        ).fetchone()
    if not row:
        return [], False
    messages, updated_at, takeover = row
    if time.time() - updated_at > config.CONVERSATION_TTL_HOURS * 3600:
        return [], False
    return json.loads(messages), _takeover_active(takeover)


def save_conversation(phone: str, messages: list, human_takeover: bool | None = False) -> None:
    """human_takeover: True (re)inicia la pausa del bot, False la quita, None la deja como está."""
    data = json.dumps(messages, ensure_ascii=False)
    with _conn() as c:
        if human_takeover is None:
            c.execute(
                "INSERT INTO conversations VALUES (?, ?, ?, 0) "
                "ON CONFLICT(phone) DO UPDATE SET messages = excluded.messages, "
                "updated_at = excluded.updated_at",
                (phone, data, time.time()),
            )
            return
        c.execute(
            "INSERT INTO conversations VALUES (?, ?, ?, ?) "
            "ON CONFLICT(phone) DO UPDATE SET messages = excluded.messages, "
            "updated_at = excluded.updated_at, human_takeover = excluded.human_takeover",
            (phone, data, time.time(), time.time() if human_takeover else 0),
        )


def set_human_takeover(phone: str, value: bool) -> None:
    with _conn() as c:
        c.execute(
            "UPDATE conversations SET human_takeover = ?, updated_at = ? WHERE phone = ?",
            (time.time() if value else 0, time.time(), phone),
        )


def add_lead(phone: str, nombre: str, interes: str, detalles: str) -> None:
    with _conn() as c:
        c.execute(
            "INSERT INTO leads (phone, nombre, interes, detalles, created_at) VALUES (?, ?, ?, ?, ?)",
            (phone, nombre, interes, detalles, time.time()),
        )


def add_escalation(phone: str, motivo: str, resumen: str) -> None:
    with _conn() as c:
        c.execute(
            "INSERT INTO escalations (phone, motivo, resumen, created_at) VALUES (?, ?, ?, ?)",
            (phone, motivo, resumen, time.time()),
        )
