from flask import Flask, render_template, request, jsonify
import requests
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity, get_jwt
)
from database import init_db, get_watchlist, save_watchlist
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
    return render_template("loginform.html")

@app.route("/admin")
def admin_page():
    return render_template("admin.html")

# --- Auth API ---

@app.route("/api/login", methods=["POST"])
def api_login():
    username = request.json.get("username")
    password = request.json.get("password")
    user = verify_user(username, password)
    if user:
        token = create_access_token(
            identity=user["username"],
            additional_claims={"role": user["role"]}
        )
        return jsonify(access_token=token)
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
@jwt_required()
def api_news():
    category = request.args.get("category", "all")
    limit    = min(int(request.args.get("limit", 50)), 100)
    articles = get_articles(category=category, limit=limit)
    return jsonify({"articles": articles, "count": len(articles)})

@app.route("/api/streams", methods=["GET"])
def api_streams():
    return jsonify({"msg": "TODO (Briefing 06)"}), 501

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("FLASK_PORT", 5001)))
