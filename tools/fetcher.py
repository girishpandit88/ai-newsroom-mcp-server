from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from urllib.parse import urlparse
from xml.etree import ElementTree

import httpx

from newsroom import Article

_DATA_PATH = Path(__file__).resolve().parents[1] / "resources" / "sample_articles.json"


def _parse_iso8601(value: str) -> datetime:
    """Parse ISO 8601 strings that may use a trailing Z for UTC."""

    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _looks_like_url(value: str) -> bool:
    parsed = urlparse(value)
    return bool(parsed.scheme and parsed.netloc)


def _normalise_timestamp(value: Optional[str]) -> str:
    if not value:
        return datetime.now(tz=timezone.utc).isoformat()

    try:
        dt = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            return _parse_iso8601(value).isoformat()
        except ValueError:
            return datetime.now(tz=timezone.utc).isoformat()

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _extract_text(element: ElementTree.Element, tag: str) -> Optional[str]:
    child = element.find(tag)
    if child is None or child.text is None:
        return None
    return child.text.strip()


def _parse_rss_feed(feed_text: str, source: str, limit: int) -> List[Article]:
    try:
        root = ElementTree.fromstring(feed_text)
    except ElementTree.ParseError as exc:
        raise ValueError(f"Unable to parse RSS feed for source '{source}': {exc}") from exc

    channel = root.find("channel")
    if channel is None:
        raise ValueError(f"RSS feed for source '{source}' does not contain a <channel> node")

    articles: List[Article] = []
    for item in channel.findall("item")[:limit or None]:
        link = _extract_text(item, "link") or source
        guid = _extract_text(item, "guid") or link
        title = html.unescape(_extract_text(item, "title") or "Untitled story")
        author = _extract_text(item, "author") or "Unknown"
        description = html.unescape(_extract_text(item, "description") or "")
        pub_date = _extract_text(item, "pubDate")

        article: Article = {
            "id": guid,
            "source": source,
            "title": title,
            "url": link,
            "timestamp": _normalise_timestamp(pub_date),
            "author": author,
            "content": description,
        }
        articles.append(article)

    return articles


def _load_articles() -> Dict[str, List[Article]]:
    if not _DATA_PATH.exists():
        return {}

    with _DATA_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    loaded: Dict[str, List[Article]] = {}
    for source, articles in data.get("sources", {}).items():
        loaded[source] = []
        for raw in articles:
            article: Article = {
                "id": raw["id"],
                "source": source,
                "title": raw["title"],
                "url": raw["url"],
                "timestamp": raw["timestamp"],
                "author": raw.get("author", "Unknown"),
                "content": raw["content"],
            }
            loaded[source].append(article)
    return loaded


def _filter_since(articles: Iterable[Article], since: Optional[str]) -> List[Article]:
    if not since:
        return list(articles)

    since_dt = _parse_iso8601(since)
    return [article for article in articles if _parse_iso8601(article["timestamp"]) >= since_dt]


def fetch_articles(source: str, since: Optional[str] = None, limit: int = 10) -> Dict[str, List[Article]]:
    """Fetch the latest news articles from a given source.

    URL sources are fetched live with ``httpx``. All other values fall back to the demo
    corpus stored in ``resources/sample_articles.json`` so the server remains usable
    offline.
    """

    if _looks_like_url(source):
        try:
            transport = httpx.HTTPTransport(retries=2)
            with httpx.Client(
                timeout=10.0,
                headers={"User-Agent": "newsroom-server/0.1"},
                follow_redirects=True,
                http2=False,
                transport=transport,
            ) as client:
                response = client.get(source)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Failed to fetch RSS feed '{source}': {exc}") from exc

        articles = _parse_rss_feed(response.text, source=source, limit=limit)
        articles = _filter_since(articles, since)
        articles = sorted(articles, key=lambda item: item["timestamp"], reverse=True)
        return {"articles": articles[:limit]}

    articles_by_source = _load_articles()
    if source not in articles_by_source:
        raise ValueError(
            f"Unknown news source '{source}'. Available sources: {sorted(articles_by_source)}"
        )

    articles = _filter_since(articles_by_source[source], since)
    articles = sorted(articles, key=lambda item: item["timestamp"], reverse=True)
    return {"articles": articles[:limit]}
