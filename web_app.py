from flask import Flask, render_template, request, jsonify, redirect
import requests
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity, get_jwt
)
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
)
from news_collector import get_articles
from auth import verify_user
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
jwt = JWTManager(app)
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
def api_login():
    username = request.json.get("username", "")
    password = request.json.get("password", "")
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    user = verify_user(username, password)
    if user:
        cleanup_audit_log()
        log_login_attempt(username, success=True, ip_address=ip)
        token = create_access_token(
            identity=user["username"],
            additional_claims={"role": user["role"]}
        )
        return jsonify(access_token=token)
    log_login_attempt(username, success=False, ip_address=ip)
    return jsonify({"msg": "Invalid credentials"}), 401

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

# --- Register ---

@app.route("/api/register", methods=["POST"])
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
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("FLASK_PORT", 5001)))
