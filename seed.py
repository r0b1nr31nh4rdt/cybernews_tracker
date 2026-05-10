import gc
import sqlite3
from database import init_db, create_user, add_news_source, get_news_sources, add_stream, get_streams

init_db()

# Users — je einzeln, damit ein Fehler nicht die DB-Connection offen lässt
for username, password, role in [
    ("admin",   "admin1234",   "admin"),
    ("analyst", "analyst1234", "analyst"),
]:
    try:
        create_user(username, password, role=role)
        print(f"  ✓ User: {username}")
    except Exception as e:
        print(f"  ~ User bereits vorhanden: {username}")

gc.collect()  # sicherstellen dass fehlgeschlagene DB-Connections geschlossen sind

# News-Quellen — nur einfügen wenn noch nicht vorhanden
existing_urls = {s[2] for s in get_news_sources(only_active=False)}

sources = [
    # Security
    ("Krebs on Security",    "https://krebsonsecurity.com/feed/",                                                                      "security"),
    ("Schneier on Security", "https://www.schneier.com/feed/atom",                                                                     "security"),
    ("The Hacker News",      "https://feeds.feedburner.com/TheHackersNews",                                                            "security"),
    ("BleepingComputer",     "https://www.bleepingcomputer.com/feed/",                                                                  "security"),
    ("SANS Internet Storm",  "https://isc.sans.edu/rssfeed_full.xml",                                                                   "security"),

    # Geopolitik
    ("Al Jazeera English",   "https://www.aljazeera.com/xml/rss/all.xml",                                                              "geopolitics"),
    ("DW World",             "https://rss.dw.com/xml/rss-en-world",                                                                    "geopolitics"),
    ("France 24 World",      "https://www.france24.com/en/rss",                                                                        "geopolitics"),
    ("Reuters World",        "https://feeds.reuters.com/reuters/worldNews",                                                             "geopolitics"),

    # Wissenschaft
    ("Ars Technica",         "https://feeds.arstechnica.com/arstechnica/index",                                                        "science"),
    ("MIT Tech Review",      "https://www.technologyreview.com/feed/",                                                                  "science"),
    ("Wired",                "https://www.wired.com/feed/rss",                                                                         "science"),

    # Netzwerke
    ("Cloudflare Blog",      "https://blog.cloudflare.com/rss/",                                                                       "networks"),
    ("RIPE NCC",             "https://labs.ripe.net/feed/",                                                                            "networks"),
    ("IETF News",            "https://www.ietf.org/blog/feed/",                                                                        "networks"),

    # DE/EU
    ("Heise Online",         "https://www.heise.de/rss/heise-atom.xml",                                                                "local"),
    ("Golem.de",             "https://rss.golem.de/rss.php?feed=RSS2.0",                                                               "local"),
    ("BSI",                  "https://www.bsi.bund.de/SiteGlobals/Functions/RSSFeed/RSSNewsfeed/RSSNewsfeed_Aktuell.xml",              "local"),
]

for name, url, category in sources:
    if url in existing_urls:
        print(f"  ~ bereits vorhanden: {name}")
        continue
    try:
        add_news_source(name, url, category)
        print(f"  ✓ {name}")
    except Exception as e:
        print(f"  ✗ {name}: {e}")

# Streams — komplett neu befüllen
conn = sqlite3.connect("users.db")
conn.execute("DELETE FROM streams")
conn.commit()
conn.close()

streams = [
    # DE
    ("Euronews DE",     "https://rakuten-euronews-4-de.samsung.wurl.tv/playlist.m3u8",                                                                                              "https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Euronews_2022.svg/512px-Euronews_2022.svg.png",         "de"),
    ("DW News DE",      "https://dwamdstream111.akamaized.net/hls/live/2017972/dwstream111/stream05/streamPlaylist.m3u8",                                                            "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Deutsche_Welle_Logo.svg/512px-Deutsche_Welle_Logo.svg.png", "de"),
    ("Tagesschau24",    "https://tagesschau.akamaized.net/hls/live/2020073/tagesschau/master.m3u8",                                                                                 "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Tagesschau_Logo.svg/512px-Tagesschau_Logo.svg.png",    "de"),
    ("Welt DE",         "https://welt-live.akamaized.net/hls/live/2011222/event1/master.m3u8",                                                                                      "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Die_Welt_Logo.svg/512px-Die_Welt_Logo.svg.png",        "de"),
    ("Phoenix DE",      "https://zdf-hls-15.akamaized.net/hls/live/2016498/de/high/master.m3u8",                                                                                    "https://upload.wikimedia.org/wikipedia/commons/thumb/8/89/Phoenix_HD_Logo_2018.svg/512px-Phoenix_HD_Logo_2018.svg.png", "de"),
    # EN
    ("Sky News EN",     "https://linear901-oo-hls0-prd-gtm.delivery.skycdp.com/17501/sde-fast-skynews/master.m3u8",                                                                 "https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/Sky-news-logo.svg/512px-Sky-news-logo.svg.png",        "en"),
    ("Euronews EN",     "https://rakuten-euronews-1-euronewseng-samsunguk.amagi.tv/playlist.m3u8",                                                                                   "https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Euronews_2022.svg/512px-Euronews_2022.svg.png",         "en"),
    ("DW News EN",      "https://dwamdstream107.akamaized.net/hls/live/2017968/dwstream107/stream05/streamPlaylist.m3u8",                                                            "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Deutsche_Welle_Logo.svg/512px-Deutsche_Welle_Logo.svg.png", "en"),
    ("France 24 EN",    "https://amg00106-france24-france24-samsunguk-qvpp8.amagi.tv/playlist/amg00106-france24-france24-samsunguk/playlist.m3u8",                                  "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/FRANCE_24_logo.svg/512px-FRANCE_24_logo.svg.png",      "en"),
    ("Al Jazeera EN",   "https://live-hls-web-aje.getaj.net/AJE/index.m3u8",                                                                                                        "https://upload.wikimedia.org/wikipedia/en/thumb/f/f2/Aljazeera_eng.svg/512px-Aljazeera_eng.svg.png",             "en"),
    ("NHK World EN",    "https://nhkwlive-ojp.akamaized.net/hls/live/2003459/nhkwlive-ojp-en/index.m3u8",                                                                           "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/NHK_World.svg/512px-NHK_World.svg.png",               "en"),
    ("TRT World EN",    "https://tv-trtworld.live.trt.com.tr/master.m3u8",                                                                                                          "https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/TRT_World_logo.svg/512px-TRT_World_logo.svg.png",      "en"),
]

for name, url, logo, language in streams:
    try:
        add_stream(name, url, logo=logo, language=language)
        print(f"  ✓ Stream: {name}")
    except Exception as e:
        print(f"  ✗ Stream {name}: {e}")

print("Done.")
