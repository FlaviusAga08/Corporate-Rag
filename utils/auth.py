import sqlite3
import bcrypt

DB_PATH = "data/users.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    import os
    os.makedirs("data", exist_ok=True)
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT    NOT NULL UNIQUE,
                email    TEXT    NOT NULL UNIQUE,
                password TEXT    NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def register_user(username: str, email: str, password: str) -> tuple[bool, str]:
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        with _get_conn() as conn:
            conn.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username.strip(), email.strip().lower(), hashed),
            )
            conn.commit()
        return True, "Cont creat cu succes."
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            return False, "Numele de utilizator există deja."
        if "email" in str(e):
            return False, "Adresa de email există deja."
        return False, "Eroare la crearea contului."


def verify_user(username_or_email: str, password: str) -> tuple[bool, str]:
    val = username_or_email.strip()
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT username, password FROM users WHERE username = ? OR email = ?",
            (val, val.lower()),
        ).fetchone()

    if row is None:
        return False, "Utilizatorul nu a fost găsit."

    if bcrypt.checkpw(password.encode(), row["password"].encode()):
        return True, row["username"]

    return False, "Parolă incorectă."
