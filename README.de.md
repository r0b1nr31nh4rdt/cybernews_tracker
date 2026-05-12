# CyberNews Tracker

Ein sicherheitsorientiertes Intelligence-Dashboard, das RSS-Feeds, Live-Nachrichtenstreams, Wetterdaten, Börsenkurse und CVE-Schwachstelleninformationen in einer einzigen Drag-and-Drop-Oberfläche bündelt.

---

## Features

| Modul | Beschreibung |
|---|---|
| **News Headlines** | RSS-Aggregation aus 17+ Quellen: Security, Geopolitik, Wissenschaft, Netzwerke, DE/EU |
| **Artikel-Viewer** | Inline-Vorschau mit Volltext-Modal, Quellenbilder |
| **Weltkarte** | Leaflet-Choropleth — Länder mit aktiven Nachrichten werden hervorgehoben |
| **Livestreams** | HLS-Streams (Al Jazeera, DW, NHK, Tagesschau) über serverseitigen Proxy |
| **Wetter** | Aktuelles Wetter + 3-Tage-Vorhersage per Postleitzahl (OpenMeteo) |
| **Kurs-Tracker** | Echtzeit-Kurse für bis zu 8 Symbole (TwelveData API) |
| **CVE des Tages** | Kritischster CVE der letzten 7 Tage aus der NIST NVD |
| **Grid-Layout** | Module verschieben, skalieren und ausblenden — Zustand wird pro User gespeichert |
| **i18n** | Deutsch / Englisch umschaltbar, serverseitige Sprachpräferenz |

### Sicherheit

- JWT-Authentifizierung (24h Laufzeit, serverseitig signiert)
- Bcrypt-Passwort-Hashing
- Flask-Talisman CSP-Header
- Flask-Limiter Rate-Limiting (Login: 10/min, Registrierung: 5/h)
- Audit-Log für alle Login-Versuche

### Admin-Panel

- Benutzerverwaltung (anlegen, Rollen vergeben, löschen)
- RSS-Quellenverwaltung (hinzufügen, aktivieren/deaktivieren, löschen)
- Stream-Verwaltung
- Audit-Log mit Filter für fehlgeschlagene Logins

---

## Tech-Stack

**Backend**
- Python 3, Flask
- Flask-JWT-Extended, Flask-Talisman, Flask-Limiter
- SQLite (via `database.py`)
- feedparser, requests, bcrypt

**Frontend**
- Vanilla JS (kein Framework)
- interact.js — Drag & Resize
- Leaflet — Karte
- HLS.js — Livestreams
- CSS Custom Properties, Dark Theme

**Externe APIs**
- [NIST NVD](https://nvd.nist.gov/) — CVE-Daten (kein Key erforderlich)
- [OpenMeteo](https://open-meteo.com/) — Wetter (kein Key erforderlich)
- [Nominatim / OpenStreetMap](https://nominatim.org/) — Geocoding (kein Key erforderlich)
- [TwelveData](https://twelvedata.com/) — Börsenkurse (Free-Tier-Key erforderlich)

---

## Schnellstart

### 1. Klonen und installieren

```bash
git clone <repo-url>
cd cybernews_tracker
pip install -r requirements.txt
```

### 2. Umgebung konfigurieren

`.env`-Datei im Projektverzeichnis anlegen:

```env
JWT_SECRET_KEY=<generieren mit: python -c "import secrets; print(secrets.token_hex(32))">
TWELVEDATA_API_KEY=<dein-key>
FLASK_PORT=5001
FLASK_DEBUG=true
```

### 3. Datenbank initialisieren und Seed-Daten einspielen

```bash
python seed.py
```

Legt die SQLite-Datenbanken an und befüllt sie mit Standard-Benutzern, Nachrichtenquellen und Streams.

**Standard-Accounts** (Passwörter nach dem ersten Login ändern):

| Benutzername | Passwort | Rolle |
|---|---|---|
| `admin` | `admin1234` | Admin |
| `analyst` | `analyst1234` | Analyst |

### 4. Starten

```bash
python web_app.py
```

Öffne [http://localhost:5001](http://localhost:5001).

---

## Projektstruktur

```
cybernews_tracker/
├── web_app.py          # Flask-App, alle API-Routen
├── database.py         # SQLite-Schema und Datenbankzugriffe
├── auth.py             # Passwortverifizierung
├── news_collector.py   # RSS-Abruf und Caching
├── seed.py             # Initialdaten (Benutzer, Quellen, Streams)
├── .env                # Umgebungskonfiguration (nicht committen)
├── static/
│   ├── dashboard.js    # App-Einstiegspunkt, Modul-Initialisierung
│   ├── grid_state.js   # Drag/Resize/Ausblend-Zustand
│   ├── grid.js         # interact.js-Integration
│   ├── news.js         # Headlines und Artikel-Viewer
│   ├── cve.js          # CVE-Widget
│   ├── stream.js       # HLS-Livestreams
│   ├── map.js          # Leaflet-Weltkarte
│   ├── weather.js      # Wetter-Widget
│   ├── stocks.js       # Kurs-Tracker
│   ├── login.js        # Auth-Modal, Nav-Zustand
│   ├── lang.js         # i18n-Umschalter
│   ├── translations.js # DE/EN-Stringtabelle
│   ├── admin.js        # Admin-Panel-Logik
│   ├── profile.js      # Profil-Seite-Logik
│   ├── logos/          # Lokale SVG-Logos für Streams
│   └── style.css       # Alle Styles, CSS Custom Properties
└── templates/
    ├── base.html       # Header, Nav, Modals, Script-Einbindungen
    ├── index.html      # Dashboard-Grid
    ├── admin.html      # Admin-Panel
    └── profile.html    # Profil / Quelleneinstellungen
```

---

## API-Endpunkte

| Methode | Pfad | Auth | Beschreibung |
|---|---|---|---|
| POST | `/api/login` | — | Authentifizierung, JWT empfangen |
| POST | `/api/register` | — | Neues Konto registrieren |
| GET | `/api/me` | JWT | Aktueller Benutzer |
| GET | `/api/news` | optional | Aggregierte RSS-Artikel |
| GET | `/api/streams` | optional | Verfügbare HLS-Streams |
| GET | `/api/stream-proxy` | — | Serverseitiger HLS-Proxy |
| GET | `/api/cve/today` | optional | Kritischster CVE der letzten 7 Tage |
| GET | `/api/weather` | — | Wetter nach Postleitzahl |
| GET | `/api/quotes` | JWT | Börsenkurse |
| GET/POST | `/api/profile/grid` | JWT | Grid-Layout-Zustand |
| GET/POST | `/api/profile/language` | JWT | Sprachpräferenz |
| GET/POST | `/api/profile/sources` | JWT | Quellen-Sichtbarkeit |
| GET/POST | `/api/watchlist` | JWT | Symbol-Watchlist |
| GET/POST | `/api/admin/users` | JWT (Admin) | Benutzerverwaltung |
| GET/POST | `/api/admin/sources` | JWT (Admin) | Quellenverwaltung |
| GET/POST | `/api/admin/streams` | JWT (Admin) | Stream-Verwaltung |
| GET | `/api/admin/audit` | JWT (Admin) | Login-Audit-Log |

---

## Ersteinrichtung: Erster Admin

Bei einer leeren Datenbank (noch kein Admin vorhanden) kann unter `/setup` der erste Admin-Account angelegt werden. Der Endpunkt sperrt sich dauerhaft, sobald ein Admin existiert.

---

## Hinweise

- HLS-Streams werden über `/api/stream-proxy` geleitet, um CORS zu umgehen und Segment-URLs umzuschreiben.
- Nachrichtenartikel werden pro Quelle im Arbeitsspeicher gecacht (5-Minuten-TTL), um RSS-Rate-Limits einzuhalten.
- Der Grid-Zustand wird für eingeloggte Benutzer serverseitig gespeichert, für anonyme Benutzer im `localStorage`.
- Die NVD-API hat ein Rate-Limit von 5 Anfragen pro 30 Sekunden — das CVE-Widget macht pro Ladevorgang maximal 2 Anfragen.
