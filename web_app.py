from flask import Flask, render_template, request, jsonify, redirect
import re
import json
from urllib.parse import urljoin, urlparse
import requests
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from database import (
    init_db, get_watchlist, save_watchlist,
    admin_exists, create_user,
    get_news_sources, add_news_source, toggle_news_source, delete_news_source,
    get_streams, add_stream, delete_stream,
    get_all_users, get_user_by_id, update_user_role, delete_user,
    log_login_attempt, get_audit_log, cleanup_audit_log,
    get_grid_state, save_grid_state,
    get_user_sources, add_user_source, delete_user_source,
    get_hidden_sources, save_hidden_sources,
    save_link, get_links, get_link_by_id, update_link_status,
    set_link_seen, snooze_link, delete_link,
    detect_content_type, fetch_link_metadata,
    get_user_ai_settings, save_user_ai_settings, tag_link_with_ai,
)
from news_collector import get_articles
from auth import verify_user
from dotenv import load_dotenv
from datetime import datetime, timedelta
import os

load_dotenv()

app = Flask(__name__)
app.config["JWT_SECRET_KEY"]              = os.getenv("JWT_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"]  = timedelta(hours=24)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=90)
jwt = JWTManager(app)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://",
)

csp = {
    "default-src": "'self'",
    "script-src": [
        "'self'",
        "cdn.jsdelivr.net",
    ],
    "style-src": [
        "'self'",
        "cdn.jsdelivr.net",
        "'unsafe-inline'",
    ],
    "img-src": [
        "'self'",
        "data:",
        "*",
    ],
    "media-src": [
        "'self'",
        "*",
        "blob:",
    ],
    "connect-src": [
        "'self'",
        "api.twelvedata.com",
        "api.open-meteo.com",
        "geocoding-api.open-meteo.com",
        "nominatim.openstreetmap.org",
        "*",
    ],
    "font-src": "'self'",
    "frame-src": "'none'",
    "worker-src": ["blob:"],
}

Talisman(
    app,
    content_security_policy=csp,
    force_https=False,
    strict_transport_security=False,
)

FLASK_PORT = os.getenv("FLASK_PORT")
TWELVEDATA_KEY = os.getenv("TWELVEDATA_API_KEY")

# --- HTML shells ---

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login_page():
    return redirect("/")

@app.route("/admin")
def admin_page():
    return render_template("admin.html")

@app.route("/setup", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def setup():
    init_db()
    if admin_exists():
        return jsonify({
            "error": "Setup bereits abgeschlossen. Dieser Endpoint ist gesperrt."
        }), 403

    if request.method == "GET":
        return render_template("setup.html")

    data     = request.json or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Username und Passwort erforderlich"}), 400
    if len(password) < 8:
        return jsonify({"error": "Passwort muss mindestens 8 Zeichen haben"}), 400

    try:
        create_user(username, password, role="admin")
        return jsonify({
            "success": True,
            "message": f"Admin '{username}' wurde angelegt. /setup ist jetzt gesperrt."
        })
    except Exception:
        return jsonify({"error": "Username bereits vergeben"}), 409

# --- Auth API ---

@app.route("/api/login", methods=["POST"])
@limiter.limit("10 per minute")
def api_login():
    username = request.json.get("username", "")
    password = request.json.get("password", "")
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    user = verify_user(username, password)
    if user:
        cleanup_audit_log()
        log_login_attempt(username, success=True, ip_address=ip)
        access_token  = create_access_token(
            identity=user["username"],
            additional_claims={"role": user["role"]}
        )
        refresh_token = create_refresh_token(identity=user["username"])
        return jsonify(access_token=access_token, refresh_token=refresh_token)
    log_login_attempt(username, success=False, ip_address=ip)
    return jsonify({"msg": "Invalid credentials"}), 401

@app.route("/api/refresh", methods=["POST"])
@jwt_required(refresh=True)
def api_refresh():
    identity     = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify(access_token=access_token)

@app.route("/api/me", methods=["GET"])
@jwt_required()
def api_me():
    username = get_jwt_identity()
    role = get_jwt().get("role")
    return jsonify(username=username, role=role)

@app.route("/api/logout", methods=["POST"])
def api_logout():
    return jsonify({"msg": "logged out"})

# --- Geo API ---

@app.route("/api/geo/countries")
def geo_countries():
    return app.send_static_file("countries.geojson")

# --- Wetter API ---

@app.route("/api/weather")
def get_weather():
    plz = request.args.get("plz", "").strip()
    if not plz:
        return jsonify({"error": "Keine PLZ angegeben"}), 400

    # Nominatim (OpenStreetMap) für PLZ → Koordinaten
    geo_resp = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"postalcode": plz, "country": "DE", "format": "json", "limit": 1},
        headers={"User-Agent": "CyberNewsTracker/1.0"},
        timeout=5
    )
    geo_data = geo_resp.json()

    if not geo_data:
        return jsonify({"error": "PLZ nicht gefunden"}), 404

    location = geo_data[0]
    lat = location["lat"]
    lon = location["lon"]
    # Ortsname aus display_name extrahieren (zweites Komma-Element = Ortsname)
    parts = location.get("display_name", plz).split(", ")
    name = parts[1] if len(parts) > 1 else plz

    weather_resp = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": ["temperature_2m", "apparent_temperature", "relative_humidity_2m",
                        "wind_speed_10m", "wind_direction_10m", "weather_code"],
            "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min"],
            "timezone": "Europe/Berlin",
            "forecast_days": 3
        },
        timeout=5
    )
    weather_data = weather_resp.json()

    return jsonify({
        "location": name,
        "current": weather_data.get("current", {}),
        "daily": weather_data.get("daily", {})
    })

# --- Sprache API ---

@app.route("/api/profile/language", methods=["GET"])
@jwt_required()
def get_language():
    from database import get_user, get_user_profile
    username = get_jwt_identity()
    db_user = get_user(username)
    if not db_user:
        return jsonify({"language": "de"})
    profile = get_user_profile(db_user[0])
    lang = profile.get("language") if profile else "de"
    return jsonify({"language": lang or "de"})

@app.route("/api/profile/language", methods=["POST"])
@jwt_required()
def save_language():
    from database import get_user, get_user_profile, create_user_profile, update_user_profile
    username = get_jwt_identity()
    db_user = get_user(username)
    if not db_user:
        return jsonify({"error": "User nicht gefunden"}), 404

    lang = request.json.get("language", "de")
    if lang not in ("de", "en"):
        return jsonify({"error": "Ungültige Sprache"}), 400

    profile = get_user_profile(db_user[0])
    if not profile:
        create_user_profile(db_user[0], language=lang)
    else:
        update_user_profile(
            db_user[0],
            language=lang,
            hobbies=profile.get("hobbies", []),
            settings=profile.get("settings", {})
        )
    return jsonify({"language": lang})

# --- Grid State API ---

@app.route("/api/profile/grid", methods=["GET"])
@jwt_required()
def get_grid():
    from database import get_user
    username = get_jwt_identity()
    db_user = get_user(username)
    if not db_user:
        return jsonify({"grid": None})
    state = get_grid_state(db_user[0])
    return jsonify({"grid": state})

@app.route("/api/profile/grid", methods=["POST"])
@jwt_required()
def save_grid():
    from database import get_user
    username = get_jwt_identity()
    db_user = get_user(username)
    if not db_user:
        return jsonify({"error": "User nicht gefunden"}), 404
    grid_state = request.json.get("grid", {})
    save_grid_state(db_user[0], grid_state)
    return jsonify({"success": True})

# --- Watchlist API ---

@app.route("/api/watchlist", methods=["GET"])
@jwt_required()
def get_user_watchlist():
    from database import get_user
    db_user = get_user(get_jwt_identity())
    if not db_user:
        return jsonify({"error": "User nicht gefunden"}), 404
    return jsonify({"watchlist": get_watchlist(db_user[0])})

@app.route("/api/watchlist", methods=["POST"])
@jwt_required()
def save_user_watchlist():
    from database import get_user
    db_user = get_user(get_jwt_identity())
    if not db_user:
        return jsonify({"error": "User nicht gefunden"}), 404
    watchlist = request.json.get("watchlist", [])[:8]
    save_watchlist(db_user[0], watchlist)
    return jsonify({"watchlist": watchlist})

# --- Kursdaten API ---

@app.route("/api/quotes")
@jwt_required()
def get_quotes():
    symbols = request.args.get("symbols", "")
    if not symbols:
        return jsonify({"error": "Keine Symbole angegeben"}), 400

    symbol_list = [s.strip() for s in symbols.split(",")][:8]
    results = []

    for symbol in symbol_list:
        try:
            resp = requests.get(
                "https://api.twelvedata.com/quote",
                params={"symbol": symbol, "apikey": TWELVEDATA_KEY},
                timeout=5
            )
            data = resp.json()
            if data.get("status") == "error":
                results.append({"symbol": symbol, "error": True})
                continue

            results.append({
                "symbol": symbol,
                "name": data.get("name", symbol),
                "price": data.get("close", "—"),
                "change": round(float(data.get("change", 0)), 2),
                "percent": round(float(data.get("percent_change", 0)), 2),
                "currency": data.get("currency", "USD"),
            })
        except Exception:
            results.append({"symbol": symbol, "error": True})

    return jsonify({"quotes": results})

# --- Platzhalter ---

@app.route("/api/news", methods=["GET"])
@jwt_required(optional=True)
def api_news():
    from database import get_user
    category = request.args.get("category", "all")
    limit    = min(int(request.args.get("limit", 100)), 100)

    user_id = None
    hidden  = []

    username = get_jwt_identity()
    if username:
        db_user = get_user(username)
        if db_user:
            user_id = db_user[0]
            hidden  = get_hidden_sources(user_id)

    articles = get_articles(
        category=category,
        limit=limit,
        user_id=user_id,
        hidden_source_ids=hidden
    )
    return jsonify({"articles": articles, "count": len(articles)})

@app.route("/api/streams", methods=["GET"])
@jwt_required(optional=True)
def api_streams():
    lang = request.args.get("lang", "de")
    streams = get_streams()
    filtered = [
        {"id": s[0], "name": s[1], "url": s[2], "logo": s[3], "language": s[4]}
        for s in streams
        if s[4] in (lang, "both")
    ]
    return jsonify({"streams": filtered})

@app.route("/api/cve/today")
@jwt_required(optional=True)
def cve_today():
    try:
        end   = datetime.utcnow()
        start = end - timedelta(days=7)

        params = {
            "cvssV3Severity": "CRITICAL",
            "pubStartDate":   start.strftime("%Y-%m-%dT%H:%M:%S.000"),
            "pubEndDate":     end.strftime("%Y-%m-%dT%H:%M:%S.999"),
            "resultsPerPage": 5,
        }

        resp = requests.get(
            "https://services.nvd.nist.gov/rest/json/cves/2.0",
            params=params,
            timeout=10,
            headers={"User-Agent": "CyberNewsTracker/1.0"}
        )
        resp.raise_for_status()
        data  = resp.json()
        vulns = data.get("vulnerabilities", [])

        if not vulns:
            params["cvssV3Severity"] = "HIGH"
            resp  = requests.get(
                "https://services.nvd.nist.gov/rest/json/cves/2.0",
                params=params,
                timeout=10,
                headers={"User-Agent": "CyberNewsTracker/1.0"}
            )
            data  = resp.json()
            vulns = data.get("vulnerabilities", [])

        if not vulns:
            return jsonify({"error": "Keine CVEs gefunden"}), 404

        def get_score(v):
            metrics = v["cve"].get("metrics", {})
            for key in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
                if key in metrics:
                    return metrics[key][0]["cvssData"].get("baseScore", 0)
            return 0

        top  = max(vulns, key=get_score)
        cve  = top["cve"]

        metrics   = cve.get("metrics", {})
        cvss_data = {}
        severity  = "UNKNOWN"
        score     = None

        for key in ["cvssMetricV31", "cvssMetricV30"]:
            if key in metrics:
                m         = metrics[key][0]
                cvss_data = m["cvssData"]
                score     = cvss_data.get("baseScore")
                severity  = cvss_data.get("baseSeverity", "UNKNOWN")
                break

        descriptions = cve.get("descriptions", [])
        description  = next(
            (d["value"] for d in descriptions if d["lang"] == "en"),
            descriptions[0]["value"] if descriptions else "Keine Beschreibung"
        )

        configs  = cve.get("configurations", [])
        products = []
        for config in configs[:1]:
            for node in config.get("nodes", [])[:3]:
                for match in node.get("cpeMatch", [])[:2]:
                    cpe = match.get("criteria", "")
                    if cpe:
                        parts = cpe.split(":")
                        if len(parts) > 4:
                            products.append(f"{parts[3]} {parts[4]}")

        return jsonify({
            "id":            cve["id"],
            "published":     cve.get("published", ""),
            "severity":      severity,
            "score":         score,
            "description":   description[:500],
            "attack_vector": cvss_data.get("attackVector", ""),
            "complexity":    cvss_data.get("attackComplexity", ""),
            "privileges":    cvss_data.get("privilegesRequired", ""),
            "products":      products[:3],
            "nvd_url":       f"https://nvd.nist.gov/vuln/detail/{cve['id']}",
            "exploitdb_url": f"https://www.exploit-db.com/search?cve={cve['id'].replace('CVE-', '')}",
        })

    except requests.exceptions.Timeout:
        return jsonify({"error": "NVD API Timeout"}), 504
    except Exception as e:
        app.logger.error(f"CVE Fehler: {e}")
        return jsonify({"error": "CVE laden fehlgeschlagen"}), 502


@app.route("/api/stream-proxy")
def stream_proxy():
    url  = request.args.get("url", "")
    base = request.args.get("base", "")
    if not url:
        return jsonify({"error": "Keine URL"}), 400
    if base and not url.startswith("http"):
        url = urljoin(base, url)
    if not url.startswith("http"):
        return jsonify({"error": "Ungültige URL"}), 400
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer":    url,
            "Origin":     url.split("/")[0] + "//" + url.split("/")[2],
            "Accept":     "*/*",
        }, stream=True)
        content_type = resp.headers.get("Content-Type", "")
        is_playlist  = (
            "mpegurl" in content_type.lower() or
            url.split("?")[0].endswith(".m3u8")
        )
        if is_playlist:
            text     = resp.text
            base_url = url.rsplit("/", 1)[0] + "/"
            def rewrite_line(line):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    if 'URI="' in stripped:
                        def rewrite_uri(m):
                            uri = m.group(1)
                            if not uri.startswith("http"):
                                uri = urljoin(base_url, uri)
                            enc      = requests.utils.quote(uri, safe="")
                            enc_base = requests.utils.quote(base_url, safe="")
                            return f'URI="/api/stream-proxy?url={enc}&base={enc_base}"'
                        return re.sub(r'URI="([^"]+)"', rewrite_uri, stripped)
                    return line
                abs_url  = urljoin(base_url, stripped)
                enc      = requests.utils.quote(abs_url, safe="")
                enc_base = requests.utils.quote(base_url, safe="")
                return f"/api/stream-proxy?url={enc}&base={enc_base}"
            rewritten = "\n".join(rewrite_line(l) for l in text.splitlines())
            response = app.response_class(
                response=rewritten,
                status=200,
                mimetype="application/vnd.apple.mpegurl"
            )
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Cache-Control"] = "no-cache"
            return response
        def generate():
            for chunk in resp.iter_content(chunk_size=8192):
                yield chunk
        response = app.response_class(
            response=generate(),
            status=resp.status_code,
            mimetype=content_type or "video/mp2t"
        )
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Cache-Control"] = "public, max-age=2"
        return response
    except requests.exceptions.Timeout:
        return jsonify({"error": "Stream Timeout"}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Stream nicht erreichbar"}), 502
    except Exception as e:
        app.logger.error(f"Stream Proxy Fehler: {e}")
        return jsonify({"error": "Proxy Fehler"}), 502

# --- Admin Helpers ---

def require_admin():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin-Zugriff erforderlich"}), 403
    return None

# --- Admin Sources API ---

@app.route("/api/admin/sources", methods=["GET"])
@jwt_required()
def admin_get_sources():
    err = require_admin()
    if err: return err
    sources = get_news_sources(only_active=False)
    return jsonify({"sources": [
        {"id": s[0], "name": s[1], "rss_url": s[2],
         "category": s[3], "active": bool(s[4])}
        for s in sources
    ]})

@app.route("/api/admin/sources", methods=["POST"])
@jwt_required()
def admin_add_source():
    err = require_admin()
    if err: return err
    data     = request.json
    name     = data.get("name", "").strip()
    rss_url  = data.get("rss_url", "").strip()
    category = data.get("category", "security")
    if not name or not rss_url:
        return jsonify({"error": "Name und URL erforderlich"}), 400
    add_news_source(name, rss_url, category)
    return jsonify({"success": True})

@app.route("/api/admin/sources/<int:source_id>", methods=["PATCH"])
@jwt_required()
def admin_toggle_source(source_id):
    err = require_admin()
    if err: return err
    active = request.json.get("active", True)
    toggle_news_source(source_id, active)
    return jsonify({"success": True})

@app.route("/api/admin/sources/<int:source_id>", methods=["DELETE"])
@jwt_required()
def admin_delete_source(source_id):
    err = require_admin()
    if err: return err
    delete_news_source(source_id)
    return jsonify({"success": True})

# --- Admin Streams API ---

@app.route("/api/admin/streams", methods=["GET"])
@jwt_required()
def admin_get_streams():
    err = require_admin()
    if err: return err
    streams = get_streams()
    return jsonify({"streams": [
        {"id": s[0], "name": s[1], "youtube_url": s[2]}
        for s in streams
    ]})

@app.route("/api/admin/streams", methods=["POST"])
@jwt_required()
def admin_add_stream():
    err = require_admin()
    if err: return err
    data = request.json
    name = data.get("name", "").strip()
    url  = data.get("youtube_url", "").strip()
    if not name or not url:
        return jsonify({"error": "Name und URL erforderlich"}), 400
    add_stream(name, url)
    return jsonify({"success": True})

@app.route("/api/admin/streams/<int:stream_id>", methods=["DELETE"])
@jwt_required()
def admin_delete_stream(stream_id):
    err = require_admin()
    if err: return err
    delete_stream(stream_id)
    return jsonify({"success": True})

# --- Admin Users API ---

@app.route("/api/admin/users", methods=["GET"])
@jwt_required()
def admin_get_users():
    err = require_admin()
    if err: return err
    users = get_all_users()
    return jsonify({"users": [
        {
            "id":         u[0],
            "username":   u[1],
            "role":       u[2],
            "email":      u[3] or "",
            "created_at": u[4] or ""
        }
        for u in users
    ]})

@app.route("/api/admin/users/<int:user_id>/role", methods=["PATCH"])
@jwt_required()
def admin_update_role(user_id):
    err = require_admin()
    if err: return err
    current_user = get_jwt_identity()
    target = get_user_by_id(user_id)
    if target and target[1] == current_user:
        return jsonify({"error": "Du kannst deine eigene Rolle nicht ändern"}), 400
    role = request.json.get("role")
    try:
        update_user_role(user_id, role)
        return jsonify({"success": True})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
def admin_delete_user(user_id):
    err = require_admin()
    if err: return err
    current_user = get_jwt_identity()
    target = get_user_by_id(user_id)
    if target and target[1] == current_user:
        return jsonify({"error": "Du kannst deinen eigenen Account nicht löschen"}), 400
    delete_user(user_id)
    return jsonify({"success": True})

@app.route("/api/admin/audit", methods=["GET"])
@jwt_required()
def admin_get_audit():
    err = require_admin()
    if err: return err
    limit = min(int(request.args.get("limit", 100)), 500)
    entries = get_audit_log(limit=limit)
    return jsonify({"entries": [
        {
            "id":        e[0],
            "timestamp": e[1],
            "username":  e[2],
            "success":   bool(e[3]),
            "ip_hash":   e[4]
        }
        for e in entries
    ]})

# --- Profile Sources API ---

@app.route("/api/profile/sources", methods=["GET"])
@jwt_required()
def profile_get_sources():
    from database import get_user
    username = get_jwt_identity()
    db_user  = get_user(username)
    if not db_user:
        return jsonify({"error": "User nicht gefunden"}), 404

    user_id        = db_user[0]
    global_sources = get_news_sources(only_active=False)
    hidden         = get_hidden_sources(user_id)
    user_sources   = get_user_sources(user_id)

    return jsonify({
        "global_sources": [
            {
                "id":       s[0],
                "name":     s[1],
                "rss_url":  s[2],
                "category": s[3],
                "active":   bool(s[4]),
                "enabled":  s[0] not in hidden
            }
            for s in global_sources if s[4]
        ],
        "user_sources": [
            {
                "id":       s[0],
                "name":     s[2],
                "rss_url":  s[3],
                "category": s[4]
            }
            for s in user_sources
        ]
    })

@app.route("/api/profile/sources/hidden", methods=["POST"])
@jwt_required()
def profile_save_hidden():
    from database import get_user
    username = get_jwt_identity()
    db_user  = get_user(username)
    if not db_user:
        return jsonify({"error": "User nicht gefunden"}), 404

    hidden = request.json.get("hidden_source_ids", [])
    save_hidden_sources(db_user[0], hidden)
    return jsonify({"success": True})

@app.route("/api/profile/sources/user", methods=["POST"])
@jwt_required()
def profile_add_user_source():
    from database import get_user
    username = get_jwt_identity()
    db_user  = get_user(username)
    if not db_user:
        return jsonify({"error": "User nicht gefunden"}), 404

    data     = request.json
    name     = data.get("name", "").strip()
    rss_url  = data.get("rss_url", "").strip()
    category = data.get("category", "security")

    if not name or not rss_url:
        return jsonify({"error": "Name und URL erforderlich"}), 400

    add_user_source(db_user[0], name, rss_url, category)
    return jsonify({"success": True})

@app.route("/api/profile/sources/user/<int:source_id>", methods=["DELETE"])
@jwt_required()
def profile_delete_user_source(source_id):
    from database import get_user
    username = get_jwt_identity()
    db_user  = get_user(username)
    if not db_user:
        return jsonify({"error": "User nicht gefunden"}), 404

    delete_user_source(source_id, db_user[0])
    return jsonify({"success": True})

# --- Link Inbox API ---

@app.route("/api/links", methods=["POST"])
@jwt_required()
def api_add_link():
    from database import get_user
    username = get_jwt_identity()
    db_user = get_user(username)
    if not db_user:
        return jsonify({"error": "User nicht gefunden"}), 404

    data = request.json or {}
    url = data.get("url", "").strip()
    source_context = data.get("source_context")

    if not url.startswith(("http://", "https://")):
        return jsonify({"error": "URL muss mit http:// oder https:// beginnen"}), 400

    content_type = detect_content_type(url)
    metadata = fetch_link_metadata(url)

    title       = metadata.get("title")
    description = metadata.get("description")
    tags        = "[]"

    ai_settings = get_user_ai_settings(db_user[0])
    if ai_settings and ai_settings.get("api_key"):
        result = tag_link_with_ai(
            url=url,
            title=title or "",
            description=description or "",
            content_type=content_type,
            api_key=ai_settings["api_key"],
            provider=ai_settings.get("provider", "claude"),
            model=ai_settings.get("model", "claude-haiku-3-5-20251001"),
        )
        if result:
            content_type = result.get("type", content_type)
            tags = json.dumps(result.get("tags", []))

    link_id = save_link(
        user_id=db_user[0],
        url=url,
        title=title,
        description=description,
        image_url=metadata.get("image_url"),
        content_type=content_type,
        tags=tags,
        source_context=source_context,
    )
    return jsonify({
        "id":           link_id,
        "title":        title,
        "content_type": content_type,
        "tags":         json.loads(tags),
    })


@app.route("/api/links", methods=["GET"])
@jwt_required()
def api_get_links():
    from database import get_user
    username = get_jwt_identity()
    db_user = get_user(username)
    if not db_user:
        return jsonify({"error": "User nicht gefunden"}), 404

    user_id = db_user[0]
    rows = get_links(
        user_id,
        status_filter=request.args.get("status"),
        type_filter=request.args.get("type"),
        tag_filter=request.args.get("tag"),
        search=request.args.get("q"),
    )
    links = [
        {
            "id":             row[0],
            "url":            row[1],
            "title":          row[2],
            "description":    row[3],
            "image_url":      row[4],
            "content_type":   row[5],
            "tags":           json.loads(row[6] or "[]"),
            "status":         row[7],
            "snoozed_until":  row[8],
            "created_at":     row[9],
            "seen_at":        row[10],
            "source_context": row[11],
        }
        for row in rows
    ]
    return jsonify({"links": links})


@app.route("/api/links/<int:link_id>", methods=["PATCH"])
@jwt_required()
def api_update_link(link_id):
    from database import get_user
    username = get_jwt_identity()
    db_user = get_user(username)
    if not db_user:
        return jsonify({"error": "User nicht gefunden"}), 404

    user_id = db_user[0]
    data = request.json or {}

    if "snooze_until" in data:
        snooze_link(link_id, user_id, data["snooze_until"])
        return jsonify({"success": True})

    if "status" in data:
        updated = update_link_status(link_id, user_id, data["status"])
        if not updated:
            return jsonify({"error": "Link nicht gefunden"}), 404
        return jsonify({"success": True})

    return jsonify({"error": "Kein gültiges Feld angegeben"}), 400


@app.route("/api/links/<int:link_id>", methods=["DELETE"])
@jwt_required()
def api_delete_link(link_id):
    from database import get_user
    username = get_jwt_identity()
    db_user = get_user(username)
    if not db_user:
        return jsonify({"error": "User nicht gefunden"}), 404

    deleted = delete_link(link_id, db_user[0])
    if not deleted:
        return jsonify({"error": "Link nicht gefunden"}), 404
    return jsonify({"success": True})


@app.route("/api/links/<int:link_id>/open", methods=["GET"])
@jwt_required()
def api_open_link(link_id):
    from database import get_user
    username = get_jwt_identity()
    db_user = get_user(username)
    if not db_user:
        return jsonify({"error": "User nicht gefunden"}), 404

    user_id = db_user[0]
    row = get_link_by_id(link_id, user_id)
    if not row:
        return jsonify({"error": "Link nicht gefunden"}), 404

    set_link_seen(link_id, user_id)
    return redirect(row[1])


# --- AI Settings API ---

@app.route("/api/settings/ai", methods=["GET"])
@jwt_required()
def api_get_ai_settings():
    from database import get_user
    username = get_jwt_identity()
    db_user = get_user(username)
    if not db_user:
        return jsonify({"error": "User nicht gefunden"}), 404

    settings = get_user_ai_settings(db_user[0])
    if not settings:
        return jsonify({"configured": False, "provider": None, "model": None})
    return jsonify({
        "configured": True,
        "provider":   settings["provider"],
        "model":      settings["model"],
    })


@app.route("/api/settings/ai", methods=["POST"])
@jwt_required()
def api_save_ai_settings():
    from database import get_user
    username = get_jwt_identity()
    db_user = get_user(username)
    if not db_user:
        return jsonify({"error": "User nicht gefunden"}), 404

    data     = request.json or {}
    provider = data.get("provider", "").strip()
    model    = data.get("model", "").strip()
    api_key  = data.get("api_key", "").strip()

    if provider != "claude":
        return jsonify({"error": "Nur 'claude' wird als Provider unterstützt"}), 400
    if not api_key:
        return jsonify({"error": "api_key darf nicht leer sein"}), 400
    if not model:
        return jsonify({"error": "model darf nicht leer sein"}), 400

    save_user_ai_settings(db_user[0], provider, model, api_key)
    return jsonify({"success": True})


# --- Register ---

@app.route("/api/register", methods=["POST"])
@limiter.limit("5 per hour")
def register():
    data     = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "")
    email    = data.get("email", "").strip() or None
    agb      = data.get("agb_accepted", False)

    if not agb:
        return jsonify({"error": "Bitte akzeptiere die Nutzungsbedingungen"}), 400
    if not username or not password:
        return jsonify({"error": "Username und Passwort erforderlich"}), 400
    if len(password) < 8:
        return jsonify({"error": "Passwort muss mindestens 8 Zeichen haben"}), 400

    try:
        create_user(username, password, role="analyst", email=email)
        return jsonify({"success": True})
    except Exception:
        return jsonify({"error": "Username bereits vergeben"}), 409

@app.route("/inbox")
def inbox_page():
    return render_template("inbox.html")

@app.route("/profile")
def profile_page():
    return render_template("profile.html")

@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/agb")
def agb():
    return render_template("agb.html")

if __name__ == "__main__":
    init_db()
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    port  = int(os.getenv("FLASK_PORT", 5001))
    app.run(debug=debug, host="0.0.0.0", port=port)
