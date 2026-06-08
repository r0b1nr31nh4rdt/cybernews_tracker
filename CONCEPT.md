# CyberNews — Link Inbox: Konzept

> Erweiterung des bestehenden CyberNews-Projekts um eine persönliche, KI-gestützte Link-Inbox für Unterrichtsmaterial, Videos, Tools und Artikel.

---

## 1. Ziel & Scope

### Problem
Im Unterricht (Zoom-Calls) werden kontinuierlich Links geteilt — Videos, News, Tools, Präsentationen — gemischt und schnell. Der Capture-Moment ist kritisch: keine Zeit für manuelle Kategorisierung. Links landen in Browser-Tabs, werden vergessen.

### Ziel
Eine Inbox, in die ein Link in unter 5 Sekunden abgelegt werden kann. Das System übernimmt automatisch: Metadaten abrufen, Content-Typ erkennen, KI-Tagging, Status-Tracking.

### Scope (MVP)
- Bookmarklet als primärer Capture-Mechanismus
- Automatisches Tagging via KI (pro User, eigener API-Key)
- Passives Status-Tracking (neu → gesehen → archiviert)
- Snooze-Funktion
- Freitextsuche + Filter nach Typ und Tags
- Multi-User (bestehende Auth-Infrastruktur)

### Out of Scope (vorerst)
- Mobile App
- Browser Extension (Manifest V3, Store-Review — zu viel Aufwand für MVP)
- E-Mail-Integration
- Volltext-Indexierung der verlinkten Seiten

---

## 2. Architektur-Übersicht

```
[Bookmarklet]
     │  POST /api/links  (JWT im Header)
     ▼
[Flask Backend]
     │
     ├─► Metadaten-Fetch (og:title, og:description, og:image)
     │
     ├─► URL-Pattern-Erkennung (schnell, kostenlos)
     │   youtube.com / vimeo   → video
     │   github.com            → tool
     │   gamma.app             → präsentation
     │   *.pdf                 → dokument
     │   default               → artikel
     │
     ├─► KI-Tagging (async, User-eigener API-Key)
     │   Input:  Titel + Beschreibung + URL + erkannter Typ
     │   Output: bestätigter Typ + 2–3 Tags (z.B. "OSINT", "Modul 4")
     │
     └─► SQLite (bestehende DB, neue Tabellen)

[Frontend — neue Inbox-Seite in CyberNews]
     ├─► Inbox-Liste (Filter: Typ, Tag, Status)
     ├─► Freitextsuche
     └─► Status-Aktionen (Snooze, Archivieren)
```

---

## 3. Datenmodell

### Neue Tabelle: `links`

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | INTEGER PK | |
| `user_id` | INTEGER FK | Verweis auf bestehende `users`-Tabelle |
| `url` | TEXT | Originale URL |
| `title` | TEXT | og:title oder Seitentitel |
| `description` | TEXT | og:description |
| `image_url` | TEXT | og:image (Thumbnail) |
| `content_type` | TEXT | `video`, `artikel`, `tool`, `dokument`, `präsentation` |
| `tags` | TEXT | JSON-Array, z.B. `["OSINT", "Modul 4"]` |
| `status` | TEXT | `neu`, `gesehen`, `archiviert` |
| `snoozed_until` | DATETIME | NULL wenn kein Snooze aktiv |
| `created_at` | DATETIME | Zeitpunkt des Speicherns |
| `seen_at` | DATETIME | Erster Klick auf den Link |
| `source_context` | TEXT | Optional: Notiz beim Speichern (z.B. "Zoom Modul 5") |

### Neue Tabelle: `user_settings`

| Spalte | Typ | Beschreibung |
|---|---|---|
| `user_id` | INTEGER FK | |
| `ai_provider` | TEXT | z.B. `claude`, `openai` |
| `ai_model` | TEXT | z.B. `claude-haiku-3-5` |
| `ai_api_key_encrypted` | TEXT | Fernet-verschlüsselter API-Key |

---

## 4. Komponenten

### 4.1 Bookmarklet

Ein einzeiliger JavaScript-Snippet, den der User einmalig in die Lesezeichen-Leiste zieht.

```javascript
javascript:(function(){
  fetch('https://cybernews.railway.app/api/links',{
    method:'POST',
    headers:{
      'Content-Type':'application/json',
      'Authorization':'Bearer '+localStorage.getItem('token')
    },
    body:JSON.stringify({url:location.href})
  }).then(()=>alert('✓ Gespeichert'));
})();
```

- Kein Install, kein Store, funktioniert in jedem Browser
- Token kommt aus dem bereits bestehenden Login (localStorage)
- Optional: kleines Popup statt `alert` für bessere UX

### 4.2 Backend-Endpunkte

| Method | Route | Beschreibung |
|---|---|---|
| POST | `/api/links` | Link speichern (triggert Metadaten + Tagging async) |
| GET | `/api/links` | Inbox abrufen (Filter: status, type, tag, q, snoozed) |
| PATCH | `/api/links/<id>` | Status ändern, Snooze setzen |
| DELETE | `/api/links/<id>` | Link löschen |
| GET | `/api/links/<id>/open` | Link öffnen + `seen_at` setzen (Redirect) |
| GET/PUT | `/api/settings` | AI-Provider + Key verwalten |

### 4.3 KI-Tagging

**Prompt-Struktur:**
```
Du bist ein Klassifikations-Assistent für Cybersecurity-Lernmaterial.

URL: {url}
Erkannter Typ: {content_type}
Titel: {title}
Beschreibung: {description}

Antworte NUR mit JSON:
{
  "type": "video|artikel|tool|dokument|präsentation",
  "tags": ["tag1", "tag2"]
}

Wähle Tags aus diesem Set wenn passend:
OSINT, Forensics, Netzwerk, Malware, Pentest, Kryptographie,
Social Engineering, Cloud, Recht & Compliance, Karriere, Off-Topic
Ergänze eigene Tags nur wenn kein passender vorhanden.
```

**Kosten-Übersicht:**

| Modell | Kosten/Link | 1.000 Links |
|---|---|---|
| claude-haiku-3-5 | ~$0.000016 | ~$0.016 |
| gpt-4o-mini | ~$0.000020 | ~$0.020 |

Tagging läuft **asynchron** — der Link ist sofort in der Inbox, Tags erscheinen nach 1–2 Sekunden.

### 4.4 API-Key-Verschlüsselung

```python
from cryptography.fernet import Fernet

# Einmalig generieren, in Umgebungsvariable speichern:
# FERNET_KEY=Fernet.generate_key()

fernet = Fernet(os.environ['FERNET_KEY'])

# Speichern:
encrypted = fernet.encrypt(api_key.encode()).decode()

# Lesen:
decrypted = fernet.decrypt(encrypted.encode()).decode()
```

Der Klartext-Key verlässt den Server nie. Nur der verschlüsselte Wert liegt in der DB.

### 4.5 Status-Logik

```
[neu]
  │
  ├─► User klickt Link          → seen_at gesetzt → Status: "gesehen"
  ├─► User klickt "Snooze"      → snoozed_until = jetzt + N Tage
  │                               Link verschwindet aus Inbox
  │                               taucht nach N Tagen wieder auf (Status: "neu")
  └─► User klickt "Archivieren" → Status: "archiviert"

[gesehen]
  └─► User klickt "Archivieren" → Status: "archiviert"

Standard-Inbox-View: Status = "neu" OR "gesehen", snoozed_until IS NULL OR < jetzt
```

---

## 5. AI-Provider-Abstraktion

Erweiterbar ohne Umbau der Kernlogik:

```python
class AIProvider:
    def tag_link(self, url, title, description, content_type) -> dict:
        raise NotImplementedError

class ClaudeProvider(AIProvider):
    def __init__(self, api_key, model="claude-haiku-3-5-20251001"):
        ...

class OpenAIProvider(AIProvider):
    def __init__(self, api_key, model="gpt-4o-mini"):
        ...

def get_provider(user_settings) -> AIProvider:
    if user_settings.ai_provider == "claude":
        return ClaudeProvider(decrypt(user_settings.ai_api_key_encrypted))
    elif user_settings.ai_provider == "openai":
        return OpenAIProvider(decrypt(user_settings.ai_api_key_encrypted))
```

MVP: nur Claude. Architektur ist von Anfang an erweiterbar.

---

## 6. Frontend — Inbox-Ansicht

**Layout:**
```
[Suchfeld]          [Filter: Typ ▾] [Filter: Tag ▾] [Status: Offen ▾]

┌─────────────────────────────────────────────────────┐
│ 🎬 [Thumbnail]  Titel des Videos                    │
│                 youtube.com · vor 2 Std.            │
│                 #OSINT  #Modul4                     │
│                 [Öffnen] [Snooze ▾] [Archivieren]  │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│ 🔧 [Icon]       Tool: Subfinder auf GitHub          │
│                 github.com · vor 1 Tag · ✓ gesehen  │
│                 #Pentest  #Recon                    │
│                 [Öffnen] [Archivieren]              │
└─────────────────────────────────────────────────────┘
```

**Snooze-Optionen:** Morgen / In 3 Tagen / Nächste Woche / Datum wählen

---

## 7. Umsetzungsschritte (priorisiert)

### Phase 1 — Backend & Datenmodell (Fundament)
1. Tabellen `links` und `user_settings` anlegen (Migration)
2. `POST /api/links` — Link speichern + Metadaten-Fetch
3. URL-Pattern-Erkennung (ohne KI, sofort verfügbar)
4. `GET /api/links` — Inbox abrufen mit Filtern
5. `PATCH /api/links/<id>` — Status + Snooze

### Phase 2 — KI-Tagging
6. Settings-Endpunkt + Verschlüsselung
7. AI-Provider-Abstraktion (Claude zuerst)
8. Async-Tagging in `POST /api/links` integrieren

### Phase 3 — Frontend
9. Inbox-Seite in CyberNews (neue Route)
10. Bookmarklet generieren + anzeigen (User-Settings-Seite)
11. Filter, Suche, Status-Aktionen

### Phase 4 — Polish
12. Snooze-Optionen (Datum-Picker)
13. Tag-Editor (nachträgliche Korrektur)
14. Optionaler Kontext beim Speichern (z.B. "Zoom Modul 5")

---

## 8. Offene Entscheidungen

| Thema | Optionen | Empfehlung |
|---|---|---|
| Snooze-Dauer (Default) | 1 Tag / 3 Tage / 1 Woche | 3 Tage |
| Tag-Set | Fix vorgegeben / frei / beides | Fix + Freitext-Ergänzung |
| Metadaten-Fetch | Serverseitig / clientseitig | Serverseitig (CORS-Probleme vermeiden) |
| Weitere KI-Provider | Nur Claude / Claude + OpenAI | Claude MVP, OpenAI in Phase 4 |
| Bookmarklet vs. Extension | Bookmarklet reicht für MVP | Bookmarklet |

---

## 9. Nicht-Ziele (bewusst weggelassen)

- Kein Volltext-Crawling der verlinkten Seiten (Komplexität, Legalität)
- Kein automatisches Zusammenfassen von Artikeln (kann später ergänzt werden)
- Keine Push-Notifications für gesnoozete Links (erstmal Polling beim Öffnen der App)
- Kein Export (Obsidian-Sync etc.) im MVP

---

*Erstellt: Juni 2026 · Projekt: CyberNews (Cybersteps IT Security)*