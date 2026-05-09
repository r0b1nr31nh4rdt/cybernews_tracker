import gc
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

# Streams — nur einfügen wenn noch nicht vorhanden
existing_stream_urls = {s[2] for s in get_streams()}

streams = [
    ("Sky News",   "https://linear901-oo-hls0-prd-gtm.delivery.skycdp.com/17501/sde-fast-skynews/master.m3u8"),
    ("Euronews",   "https://dash4.antik.sk/live/test_euronews/playlist.m3u8"),
    ("DW News",    "https://dwamdstream103.akamaized.net/hls/live/2015526/dwstream103/master.m3u8"),
    ("France 24",  "https://amg00106-france24-france24-samsunguk-qvpp8.amagi.tv/playlist/amg00106-france24-france24-samsunguk/playlist.m3u8"),
    ("Al Arabiya", "https://live.alarabiya.net/alarabiapublish/alarabiya.smil/playlist.m3u8"),
    ("Al Jazeera", "https://live-hls-apps-aje-fa.getaj.net/AJE/index.m3u8"),
]

for name, url in streams:
    if url in existing_stream_urls:
        print(f"  ~ bereits vorhanden: {name}")
        continue
    try:
        add_stream(name, url)
        print(f"  ✓ {name}")
    except Exception as e:
        print(f"  ✗ {name}: {e}")

print("Done.")
