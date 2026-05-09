import sqlite3
import bcrypt
import json
import hashlib

DB_PATH = "users.db"

# ── Init ──────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY,
            username   TEXT UNIQUE,
            password   TEXT,
            role       TEXT,
            email      TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migration: Spalten nachrüsten falls Tabelle bereits ohne sie existiert
    for migration in [
        "ALTER TABLE users ADD COLUMN email TEXT",
        "ALTER TABLE users ADD COLUMN created_at TEXT",
    ]:
        try:
            cursor.execute(migration)
        except Exception:
            pass  # Spalte existiert bereits

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE,
            language TEXT,
            hobbies TEXT,
            settings TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_sources (
            id INTEGER PRIMARY KEY,
            name TEXT,
            rss_url TEXT,
            category TEXT,
            active INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS streams (
            id INTEGER PRIMARY KEY,
            name TEXT,
            youtube_url TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id         INTEGER PRIMARY KEY,
            timestamp  TEXT DEFAULT (datetime('now')),
            username   TEXT,
            success    INTEGER,
            ip_hash    TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_favorites (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            source_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (source_id) REFERENCES news_sources (id)
        )
    """)

    conn.commit()
    conn.close()

# ── Users ─────────────────────────────────────────────

def admin_exists():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def create_user(username, password, role="analyst", email=None):
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, password, role, email, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
        (username, hashed, role, email)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id

def get_user(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, role, email, created_at
        FROM users
        ORDER BY created_at DESC
    """)
    users = cursor.fetchall()
    conn.close()
    return users

def get_user_by_id(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_user_role(user_id, role):
    if role not in ("admin", "analyst"):
        raise ValueError("Ungültige Rolle")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
    conn.commit()
    conn.close()

def log_login_attempt(username, success, ip_address):
    ip_hash = hashlib.sha256(
        (ip_address or "unknown").encode()
    ).hexdigest()[:16]
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO audit_log (username, success, ip_hash) VALUES (?, ?, ?)",
        (username, 1 if success else 0, ip_hash)
    )
    conn.commit()
    conn.close()

def get_audit_log(limit=100):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, timestamp, username, success, ip_hash
        FROM audit_log
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))
    entries = cursor.fetchall()
    conn.close()
    return entries

def cleanup_audit_log():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM audit_log
        WHERE timestamp < datetime('now', '-90 days')
    """)
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted

def delete_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    cursor.execute("DELETE FROM user_profiles WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM user_favorites WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# ── User Profiles ─────────────────────────────────────

def create_user_profile(user_id, language=None, hobbies=None, settings=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_profiles VALUES (?, ?, ?, ?, ?)",
                   (None, user_id,
                    language,
                    json.dumps(hobbies or []),
                    json.dumps(settings or {})))
    conn.commit()
    conn.close()

def get_user_profile(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
    profile = cursor.fetchone()
    conn.close()
    if profile:
        return {
            "language": profile[2],
            "hobbies": json.loads(profile[3]),
            "settings": json.loads(profile[4])
        }
    return None

def update_user_profile(user_id, language=None, hobbies=None, settings=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE user_profiles
        SET language = ?, hobbies = ?, settings = ?
        WHERE user_id = ?
    """, (language, json.dumps(hobbies or []), json.dumps(settings or {}), user_id))
    conn.commit()
    conn.close()

# ── News Sources ──────────────────────────────────────

def add_news_source(name, rss_url, category):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO news_sources VALUES (?, ?, ?, ?, ?)",
                   (None, name, rss_url, category, 1))
    conn.commit()
    conn.close()

def get_news_sources(only_active=True):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if only_active:
        cursor.execute("SELECT * FROM news_sources WHERE active = 1")
    else:
        cursor.execute("SELECT * FROM news_sources")
    sources = cursor.fetchall()
    conn.close()
    return sources

def toggle_news_source(source_id, active):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE news_sources SET active = ? WHERE id = ?",
                   (1 if active else 0, source_id))
    conn.commit()
    conn.close()

def delete_news_source(source_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM news_sources WHERE id = ?", (source_id,))
    cursor.execute("DELETE FROM user_favorites WHERE source_id = ?", (source_id,))
    conn.commit()
    conn.close()

# ── Streams ───────────────────────────────────────────

def add_stream(name, youtube_url):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO streams VALUES (?, ?, ?)",
                   (None, name, youtube_url))
    conn.commit()
    conn.close()

def get_streams():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM streams")
    streams = cursor.fetchall()
    conn.close()
    return streams

def delete_stream(stream_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM streams WHERE id = ?", (stream_id,))
    conn.commit()
    conn.close()

# ── User Favorites ────────────────────────────────────

def add_favorite(user_id, source_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_favorites VALUES (?, ?, ?)",
                   (None, user_id, source_id))
    conn.commit()
    conn.close()

def get_favorites(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ns.* FROM news_sources ns
        JOIN user_favorites uf ON ns.id = uf.source_id
        WHERE uf.user_id = ?
    """, (user_id,))
    favorites = cursor.fetchall()
    conn.close()
    return favorites

def remove_favorite(user_id, source_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_favorites WHERE user_id = ? AND source_id = ?",
                   (user_id, source_id))
    conn.commit()
    conn.close()

# ── Watchlist ──────────────────────────────────────

def get_watchlist(user_id):
    profile = get_user_profile(user_id)
    if not profile:
        return []
    settings = profile.get("settings", {})
    return settings.get("watchlist", [])

def get_grid_state(user_id):
    profile = get_user_profile(user_id)
    if not profile:
        return None
    return profile.get("settings", {}).get("grid", None)

def save_grid_state(user_id, grid_state):
    profile = get_user_profile(user_id)
    if not profile:
        create_user_profile(user_id, settings={"grid": grid_state})
        return
    settings = profile.get("settings", {})
    settings["grid"] = grid_state
    update_user_profile(
        user_id,
        language=profile.get("language"),
        hobbies=profile.get("hobbies", []),
        settings=settings
    )

def save_watchlist(user_id, watchlist):
    profile = get_user_profile(user_id)
    if not profile:
        create_user_profile(user_id, settings={"watchlist": watchlist})
        return
    settings = profile.get("settings", {})
    settings["watchlist"] = watchlist
    update_user_profile(
        user_id,
        language=profile.get("language"),
        hobbies=profile.get("hobbies", []),
        settings=settings
    )