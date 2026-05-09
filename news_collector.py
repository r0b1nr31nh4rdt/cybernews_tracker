import feedparser
import time
from datetime import datetime, timezone
from database import get_news_sources

_cache = {}
CACHE_TTL = 300  # 5 Minuten

def fetch_feed(source):
    """Einen einzelnen RSS-Feed abrufen und parsen."""
    source_id, name, rss_url, category, active = source

    now = time.time()
    if source_id in _cache:
        cached_at, articles = _cache[source_id]
        if now - cached_at < CACHE_TTL:
            return articles

    try:
        feed = feedparser.parse(rss_url)
        articles = []

        for entry in feed.entries[:15]:
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    published = datetime(
                        *entry.published_parsed[:6],
                        tzinfo=timezone.utc
                    ).isoformat()
                except Exception:
                    pass

            articles.append({
                "id":        entry.get("id", entry.get("link", "")),
                "title":     entry.get("title", "Kein Titel"),
                "summary":   entry.get("summary", ""),
                "link":      entry.get("link", ""),
                "published": published,
                "source":    name,
                "source_id": source_id,
                "category":  category,
            })

        _cache[source_id] = (now, articles)
        return articles

    except Exception as e:
        print(f"Feed-Fehler [{name}]: {e}")
        return []


def get_articles(category=None, limit=50):
    """Artikel aller aktiven Quellen laden, optional nach Kategorie filtern."""
    sources = get_news_sources(only_active=True)
    all_articles = []

    for source in sources:
        if category and category != "all" and source[3] != category:
            continue
        all_articles.extend(fetch_feed(source))

    all_articles.sort(
        key=lambda a: a["published"] or "",
        reverse=True
    )

    return all_articles[:limit]
