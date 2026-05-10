import feedparser
import re
import time
from datetime import datetime, timezone
from database import get_news_sources

_cache = {}
CACHE_TTL = 300  # 5 Minuten

def fetch_feed(source, cache_key=None):
    """Einen einzelnen RSS-Feed abrufen und parsen."""
    source_id, name, rss_url, category, active = source
    key = cache_key if cache_key is not None else source_id

    now = time.time()
    if key in _cache:
        cached_at, articles = _cache[key]
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

            image = None
            if hasattr(entry, "media_content") and entry.media_content:
                image = entry.media_content[0].get("url") or None
            elif hasattr(entry, "enclosures") and entry.enclosures:
                enc = entry.enclosures[0]
                if enc.get("type", "").startswith("image"):
                    image = enc.get("href")
            elif hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
                image = entry.media_thumbnail[0].get("url")
            if not image:
                content_html = ""
                if hasattr(entry, "content") and entry.content:
                    content_html = entry.content[0].get("value", "")
                if not content_html:
                    content_html = entry.get("summary", "")
                m = re.search(r'<img[^>]+src=["\']?(https?://[^"\'> ]+)["\']?', content_html)
                if m:
                    image = m.group(1)

            articles.append({
                "id":        entry.get("id", entry.get("link", "")),
                "title":     entry.get("title", "Kein Titel"),
                "summary":   entry.get("summary", ""),
                "link":      entry.get("link", ""),
                "published": published,
                "source":    name,
                "source_id": source_id,
                "category":  category,
                "image":     image,
            })

        _cache[key] = (now, articles)
        return articles

    except Exception as e:
        print(f"Feed-Fehler [{name}]: {e}")
        return []


def get_articles(category=None, limit=50, user_id=None, hidden_source_ids=None):
    """Artikel laden — optional mit User-Kontext."""
    from database import get_user_sources

    sources = get_news_sources(only_active=True)
    all_articles = []
    hidden = set(hidden_source_ids or [])

    for source in sources:
        if source[0] in hidden:
            continue
        if category and category != "all" and source[3] != category:
            continue
        all_articles.extend(fetch_feed(source))

    if user_id:
        user_sources = get_user_sources(user_id)
        for source in user_sources:
            if category and category != "all" and source[4] != category:
                continue
            # user_sources: (id, user_id, name, rss_url, category, active)
            # normalisieren auf news_sources Format: (id, name, rss_url, category, active)
            normalized = (source[0], source[2], source[3], source[4], source[5])
            all_articles.extend(fetch_feed(normalized, cache_key=f"u{source[0]}"))

    all_articles.sort(
        key=lambda a: a["published"] or "",
        reverse=True
    )

    return all_articles[:limit]
