import sqlite3
import bcrypt
import json
import hashlib
import os
import requests
from cryptography.fernet import Fernet

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
            youtube_url TEXT,
            logo TEXT,
            language TEXT DEFAULT 'both'
        )
    """)

    for migration in [
        "ALTER TABLE streams ADD COLUMN logo TEXT",
        "ALTER TABLE streams ADD COLUMN language TEXT DEFAULT 'both'",
    ]:
        try:
            cursor.execute(migration)
        except Exception:
            pass

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
        CREATE TABLE IF NOT EXISTS user_sources (
            id       INTEGER PRIMARY KEY,
            user_id  INTEGER,
            name     TEXT,
            rss_url  TEXT,
            category TEXT,
            active   INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id)
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS links (
            id              INTEGER PRIMARY KEY,
            user_id         INTEGER NOT NULL,
            url             TEXT NOT NULL,
            title           TEXT,
            description     TEXT,
            image_url       TEXT,
            content_type    TEXT DEFAULT 'artikel',
            tags            TEXT DEFAULT '[]',
            status          TEXT DEFAULT 'neu',
            snoozed_until   TEXT,
            created_at      TEXT DEFAULT (datetime('now')),
            seen_at         TEXT,
            source_context  TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            id                    INTEGER PRIMARY KEY,
            user_id               INTEGER UNIQUE NOT NULL,
            ai_provider           TEXT DEFAULT 'claude',
            ai_model              TEXT DEFAULT 'claude-haiku-3-5-20251001',
            ai_api_key_encrypted  TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
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

def add_stream(name, youtube_url, logo=None, language="both"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO streams (name, youtube_url, logo, language) VALUES (?, ?, ?, ?)",
        (name, youtube_url, logo, language)
    )
    conn.commit()
    conn.close()

def get_streams():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, youtube_url, logo, language FROM streams")
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

def get_user_sources(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM user_sources WHERE user_id = ? AND active = 1",
        (user_id,)
    )
    sources = cursor.fetchall()
    conn.close()
    return sources

def add_user_source(user_id, name, rss_url, category):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_sources (user_id, name, rss_url, category) VALUES (?, ?, ?, ?)",
        (user_id, name, rss_url, category)
    )
    conn.commit()
    conn.close()

def delete_user_source(source_id, user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM user_sources WHERE id = ? AND user_id = ?",
        (source_id, user_id)
    )
    conn.commit()
    conn.close()

def get_hidden_sources(user_id):
    profile = get_user_profile(user_id)
    if not profile:
        return []
    return profile.get("settings", {}).get("hidden_sources", [])

def save_hidden_sources(user_id, hidden_source_ids):
    profile = get_user_profile(user_id)
    if not profile:
        create_user_profile(user_id, settings={"hidden_sources": hidden_source_ids})
        return
    settings = profile.get("settings", {})
    settings["hidden_sources"] = hidden_source_ids
    update_user_profile(
        user_id,
        language=profile.get("language"),
        hobbies=profile.get("hobbies", []),
        settings=settings
    )

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

# ── Link Inbox ────────────────────────────────────────

def detect_content_type(url: str) -> str:
    """Erkennt Content-Typ anhand der URL. Kein HTTP-Request nötig."""
    url_lower = url.lower()
    if any(x in url_lower for x in ["youtube.com", "youtu.be", "vimeo.com"]):
        return "video"
    if "github.com" in url_lower:
        return "tool"
    if "gamma.app" in url_lower:
        return "präsentation"
    if url_lower.endswith(".pdf"):
        return "dokument"
    return "artikel"


def fetch_link_metadata(url: str) -> dict:
    """Fetcht og:-Metadaten. Gibt leeres Dict zurück bei Fehler."""
    try:
        from html.parser import HTMLParser

        class _MetaParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.og = {}
                self._title_text = None
                self._in_title = False

            def handle_starttag(self, tag, attrs):
                attrs_dict = dict(attrs)
                if tag == "meta":
                    prop = attrs_dict.get("property", "") or attrs_dict.get("name", "")
                    content = attrs_dict.get("content", "")
                    if prop == "og:title":
                        self.og["title"] = content
                    elif prop == "og:description":
                        self.og["description"] = content
                    elif prop == "og:image":
                        self.og["image_url"] = content
                elif tag == "title":
                    self._in_title = True

            def handle_endtag(self, tag):
                if tag == "title":
                    self._in_title = False

            def handle_data(self, data):
                if self._in_title and self._title_text is None:
                    self._title_text = data.strip()

        resp = requests.get(url, timeout=5, headers={"User-Agent": "CyberNewsTracker/1.0"})
        resp.raise_for_status()

        parser = _MetaParser()
        parser.feed(resp.text[:50000])

        result = {}
        if parser.og.get("title"):
            result["title"] = parser.og["title"]
        elif parser._title_text:
            result["title"] = parser._title_text
        if parser.og.get("description"):
            result["description"] = parser.og["description"]
        if parser.og.get("image_url"):
            result["image_url"] = parser.og["image_url"]
        return result
    except Exception:
        return {}


def save_link(user_id, url, title, description, image_url, content_type, tags="[]", source_context=None) -> int:
    """Speichert einen Link, gibt die neue id zurück."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO links (user_id, url, title, description, image_url, content_type, tags, source_context)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, url, title, description, image_url, content_type, tags, source_context)
    )
    link_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return link_id


def get_links(user_id, status_filter=None, type_filter=None, tag_filter=None, search=None) -> list:
    """
    Gibt Links zurück. Standard: status IN ('neu','gesehen') AND (snoozed_until IS NULL OR snoozed_until < now).
    Filter sind optional und kombinierbar.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
        SELECT id, url, title, description, image_url, content_type, tags, status,
               snoozed_until, created_at, seen_at, source_context
        FROM links
        WHERE user_id = ?
    """
    params = [user_id]

    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    else:
        query += " AND status IN ('neu', 'gesehen') AND (snoozed_until IS NULL OR snoozed_until < datetime('now'))"

    if type_filter:
        query += " AND content_type = ?"
        params.append(type_filter)

    if tag_filter:
        query += ' AND tags LIKE ?'
        params.append(f'%"{tag_filter}"%')

    if search:
        query += " AND (title LIKE ? OR description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY created_at DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_link_by_id(link_id, user_id):
    """Gibt einen einzelnen Link zurück, nur wenn user_id stimmt."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, url, title, description, image_url, content_type, tags, status, "
        "snoozed_until, created_at, seen_at, source_context FROM links WHERE id = ? AND user_id = ?",
        (link_id, user_id)
    )
    row = cursor.fetchone()
    conn.close()
    return row


def update_link_status(link_id, user_id, status) -> bool:
    """Setzt status. user_id zur Sicherheit mitprüfen (kein fremder Zugriff)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE links SET status = ? WHERE id = ? AND user_id = ?",
        (status, link_id, user_id)
    )
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def set_link_seen(link_id, user_id):
    """Setzt seen_at = now, status = 'gesehen' — nur wenn seen_at noch NULL."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE links SET seen_at = datetime('now'), status = 'gesehen' "
        "WHERE id = ? AND user_id = ? AND seen_at IS NULL",
        (link_id, user_id)
    )
    conn.commit()
    conn.close()


def snooze_link(link_id, user_id, snooze_until_iso: str):
    """Setzt snoozed_until. Format: ISO-Datetime-String."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE links SET snoozed_until = ? WHERE id = ? AND user_id = ?",
        (snooze_until_iso, link_id, user_id)
    )
    conn.commit()
    conn.close()


def delete_link(link_id, user_id) -> bool:
    """Löscht Link — nur wenn user_id stimmt."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM links WHERE id = ? AND user_id = ?",
        (link_id, user_id)
    )
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# ── Verschlüsselung ───────────────────────────────────

def _get_fernet() -> Fernet:
    key = os.getenv("FERNET_KEY")
    if not key:
        raise RuntimeError("FERNET_KEY nicht gesetzt")
    return Fernet(key.encode())

def encrypt_api_key(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()

def decrypt_api_key(ciphertext: str) -> str:
    return _get_fernet().decrypt(ciphertext.encode()).decode()

# ── User AI Settings ──────────────────────────────────

def get_user_ai_settings(user_id: int) -> dict | None:
    """Gibt AI-Settings zurück, API-Key bereits entschlüsselt. None wenn nicht konfiguriert."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ai_provider, ai_model, ai_api_key_encrypted FROM user_settings WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row or not row[2]:
        return None
    try:
        api_key = decrypt_api_key(row[2])
    except Exception:
        return None
    return {"provider": row[0], "model": row[1], "api_key": api_key}


def save_user_ai_settings(user_id: int, provider: str, model: str, api_key_plaintext: str):
    """Speichert oder aktualisiert AI-Settings. Key wird verschlüsselt abgelegt."""
    encrypted = encrypt_api_key(api_key_plaintext)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """INSERT OR REPLACE INTO user_settings (user_id, ai_provider, ai_model, ai_api_key_encrypted)
           VALUES (?, ?, ?, ?)""",
        (user_id, provider, model, encrypted)
    )
    conn.commit()
    conn.close()

# ── KI-Tagging ────────────────────────────────────────

def tag_link_with_ai(
    url: str,
    title: str,
    description: str,
    content_type: str,
    api_key: str,
    provider: str = "claude",
    model: str = "claude-haiku-3-5-20251001",
) -> dict:
    """
    Ruft die KI-API auf und gibt zurück:
    { "type": "video|artikel|tool|dokument|präsentation", "tags": ["tag1", "tag2"] }
    Bei Fehler: leeres Dict, kein Exception-Raise.
    """
    try:
        prompt = (
            "Du bist ein Klassifikations-Assistent für Cybersecurity-Lernmaterial.\n\n"
            f"URL: {url}\n"
            f"Erkannter Typ: {content_type}\n"
            f"Titel: {title}\n"
            f"Beschreibung: {description}\n\n"
            "Antworte NUR mit einem JSON-Objekt, ohne Markdown, ohne Erklärung:\n"
            '{\n  "type": "video|artikel|tool|dokument|präsentation",\n  "tags": ["tag1", "tag2"]\n}\n\n'
            "Wähle Tags bevorzugt aus dieser Liste:\n"
            "OSINT, Forensics, Netzwerk, Malware, Pentest, Kryptographie,\n"
            "Social Engineering, Cloud, Recht & Compliance, Karriere, Off-Topic\n\n"
            "Ergänze eigene Tags nur wenn kein passender vorhanden ist.\n"
            "Maximal 3 Tags."
        )

        if provider == "claude":
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model,
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            return json.loads(raw)

        return {}
    except Exception:
        return {}