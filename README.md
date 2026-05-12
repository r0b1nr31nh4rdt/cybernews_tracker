# CyberNews Tracker

A security-focused intelligence dashboard that aggregates RSS feeds, live news streams, weather, stock data, and CVE vulnerability information into a single drag-and-drop interface.

---

## Features

| Module | Description |
|---|---|
| **News Headlines** | RSS aggregation from 17+ sources across Security, Geopolitics, Science, Networks, DE/EU |
| **Article Viewer** | Inline preview with full-text modal, source images |
| **World Map** | Leaflet choropleth — countries with active news highlighted |
| **Live Streams** | HLS streams (Al Jazeera, DW, NHK, Tagesschau) via server-side proxy |
| **Weather** | Current conditions + 3-day forecast via postal code (OpenMeteo) |
| **Stock Tracker** | Real-time quotes for up to 8 symbols (TwelveData API) |
| **CVE of the Day** | Highest-severity CVE of the last 7 days from NIST NVD |
| **Grid Layout** | Drag, resize, and hide modules — state persisted per user |
| **i18n** | German / English toggle, server-side language preference |

### Security

- JWT authentication (24h expiry, server-signed)
- Bcrypt password hashing
- Flask-Talisman CSP headers
- Flask-Limiter rate limiting (login: 10/min, register: 5/h)
- Audit log for all login attempts

### Admin Panel

- User management (create, assign roles, delete)
- RSS source management (add, toggle active, delete)
- Stream management
- Audit log viewer with failed-login filter

---

## Tech Stack

**Backend**
- Python 3, Flask
- Flask-JWT-Extended, Flask-Talisman, Flask-Limiter
- SQLite (via `database.py`)
- feedparser, requests, bcrypt

**Frontend**
- Vanilla JS (no framework)
- interact.js — drag & resize
- Leaflet — map
- HLS.js — live streams
- CSS custom properties, dark theme

**External APIs**
- [NIST NVD](https://nvd.nist.gov/) — CVE data (no key required)
- [OpenMeteo](https://open-meteo.com/) — weather (no key required)
- [Nominatim / OpenStreetMap](https://nominatim.org/) — geocoding (no key required)
- [TwelveData](https://twelvedata.com/) — stock quotes (free tier key required)

---

## Quick Start

### 1. Clone and install

```bash
git clone <repo-url>
cd cybernews_tracker
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file in the project root:

```env
JWT_SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
TWELVEDATA_API_KEY=<your-key>
FLASK_PORT=5001
FLASK_DEBUG=true
```

### 3. Initialize database and seed data

```bash
python seed.py
```

This creates the SQLite databases and inserts default users, news sources, and streams.

**Default accounts** (change passwords after first login):

| Username | Password | Role |
|---|---|---|
| `admin` | `admin1234` | Admin |
| `analyst` | `analyst1234` | Analyst |

### 4. Run

```bash
python web_app.py
```

Open [http://localhost:5001](http://localhost:5001).

---

## Project Structure

```
cybernews_tracker/
├── web_app.py          # Flask app, all API routes
├── database.py         # SQLite schema and queries
├── auth.py             # Password verification
├── news_collector.py   # RSS fetching and caching
├── seed.py             # Initial data (users, sources, streams)
├── .env                # Environment config (not committed)
├── static/
│   ├── dashboard.js    # App entry point, module init
│   ├── grid_state.js   # Drag/resize/hide state management
│   ├── grid.js         # interact.js integration
│   ├── news.js         # Headlines and article viewer
│   ├── cve.js          # CVE widget
│   ├── stream.js       # HLS live streams
│   ├── map.js          # Leaflet world map
│   ├── weather.js      # Weather widget
│   ├── stocks.js       # Stock tracker
│   ├── login.js        # Auth modal, nav state
│   ├── lang.js         # i18n toggle
│   ├── translations.js # DE/EN string table
│   ├── admin.js        # Admin panel logic
│   ├── profile.js      # Profile page logic
│   ├── logos/          # Local SVG logos for streams
│   └── style.css       # All styles, CSS custom properties
└── templates/
    ├── base.html       # Header, nav, modals, script includes
    ├── index.html      # Dashboard grid
    ├── admin.html      # Admin panel
    └── profile.html    # Profile / source settings
```

---

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/login` | — | Authenticate, receive JWT |
| POST | `/api/register` | — | Register new account |
| GET | `/api/me` | JWT | Current user info |
| GET | `/api/news` | optional | Aggregated RSS articles |
| GET | `/api/streams` | optional | Available HLS streams |
| GET | `/api/stream-proxy` | — | Server-side HLS proxy |
| GET | `/api/cve/today` | optional | Highest CVE last 7 days |
| GET | `/api/weather` | — | Weather by postal code |
| GET | `/api/quotes` | JWT | Stock quotes |
| GET/POST | `/api/profile/grid` | JWT | Grid layout state |
| GET/POST | `/api/profile/language` | JWT | Language preference |
| GET/POST | `/api/profile/sources` | JWT | Source visibility |
| GET/POST | `/api/watchlist` | JWT | Symbol watchlist |
| GET/POST | `/api/admin/users` | JWT (admin) | User management |
| GET/POST | `/api/admin/sources` | JWT (admin) | Source management |
| GET/POST | `/api/admin/streams` | JWT (admin) | Stream management |
| GET | `/api/admin/audit` | JWT (admin) | Login audit log |

---

## Setup: First-Time Admin

If the database is fresh (no admin yet), visit `/setup` to create the first admin account. The endpoint locks itself permanently once an admin exists.

---

## Notes

- HLS streams are proxied through `/api/stream-proxy` to handle CORS and rewrite segment URLs.
- News articles are cached in memory per source (5-minute TTL) to respect RSS rate limits.
- Grid state is saved server-side for logged-in users, in `localStorage` for anonymous users.
- The NVD API has a rate limit of 5 requests per 30 seconds — the CVE widget makes at most 2 requests per load.
