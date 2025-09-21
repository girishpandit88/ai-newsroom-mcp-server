from __future__ import annotations

import math
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Set

from newsroom import Article, RankedStory, TagSummary


def _ensure_str_set(values: Iterable[Any]) -> Set[str]:
    return {str(value).strip().lower() for value in values if isinstance(value, str) and value.strip()}


def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value or not isinstance(value, str):
        return None

    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _validate_summary(summary: TagSummary) -> Optional[TagSummary]:
    required_keys = {"tag", "canonical_id", "category", "highlights", "article_ids"}
    if not required_keys.issubset(summary.keys()):
        missing = required_keys - summary.keys()
        print(f"[newsroom] skipping summary missing keys: {missing}", file=sys.stderr)
        return None

    highlights = [text for text in summary["highlights"] if isinstance(text, str) and text.strip()]
    article_ids = [article_id for article_id in summary["article_ids"] if isinstance(article_id, str) and article_id]

    if not highlights or not article_ids:
        print("[newsroom] skipping summary without highlights or article ids", file=sys.stderr)
        return None

    validated: TagSummary = {
        "tag": summary["tag"],
        "canonical_id": summary["canonical_id"],
        "category": summary["category"],
        "highlights": highlights,
        "article_ids": article_ids,
    }
    return validated


def _recency_weight(timestamp: Optional[str], *, now: Optional[datetime] = None) -> float:
    if now is None:
        now = datetime.now(tz=timezone.utc)
    published = _parse_timestamp(timestamp)
    if not published:
        return 0.0

    age_hours = max((now - published).total_seconds() / 3600.0, 0.0)
    return math.exp(-age_hours / 48.0)


def _highlight_density(highlights: List[str]) -> float:
    combined = " ".join(highlights)
    words = combined.split()
    if not words:
        return 0.0
    return min(len(words) / 80.0, 1.0)


def personalize_and_rank(
    user_profile: Dict[str, Any],
    summaries: List[TagSummary],
    articles: Optional[List[Article]] = None,
) -> Dict[str, List[RankedStory]]:
    """Rank stories by matching tag summaries to user preferences.

    The scorer relies on simple heuristics instead of LLMs. Each summary is validated
    before ranking to ensure downstream stability.
    """

    preferred_topics = _ensure_str_set(user_profile.get("preferred_topics", []))
    priority_entities = _ensure_str_set(user_profile.get("priority_entities", []))
    favourite_sources = _ensure_str_set(user_profile.get("favourite_sources", []))
    blocked_sources = _ensure_str_set(user_profile.get("blocked_sources", []))

    article_lookup = {article["id"]: article for article in articles or [] if article.get("id")}

    ranked: List[RankedStory] = []
    now = datetime.now(tz=timezone.utc)

    for raw_summary in summaries:
        summary = _validate_summary(raw_summary)
        if not summary:
            continue

        summary_tag_lower = summary["tag"].lower()
        category_lower = summary["category"].lower()
        highlight_text = " ".join(summary["highlights"]).lower()

        topic_match = any(topic in category_lower for topic in preferred_topics)
        entity_match = summary_tag_lower in priority_entities
        keyword_match = any(topic in highlight_text for topic in preferred_topics)
        highlight_strength = _highlight_density(summary["highlights"])

        for article_id in summary["article_ids"]:
            article = article_lookup.get(article_id)
            source_lower = article["source"].lower() if article and isinstance(article.get("source"), str) else ""

            if source_lower and source_lower in blocked_sources:
                continue

            score = 0.6  # Baseline score ensuring deterministic ordering
            reasons: List[str] = [f"Entity focus: {summary['tag']}"]

            if topic_match:
                score += 1.0
                reasons.append("Matches preferred topic")
            if entity_match:
                score += 1.2
                reasons.append("Priority entity")
            if keyword_match and not topic_match:
                score += 0.5
                reasons.append("Highlight matches interest")

            score += 0.8 * highlight_strength
            if highlight_strength > 0.6:
                reasons.append("Rich highlight")

            if article:
                timestamp = article.get("timestamp") if isinstance(article.get("timestamp"), str) else None
                recency = _recency_weight(timestamp, now=now)
                score += 0.7 * recency
                if recency > 0.5:
                    reasons.append("Recent coverage")

                if favourite_sources and source_lower in favourite_sources:
                    score += 0.4
                    reasons.append("Favourite source")

                title = article.get("title", summary["tag"])
                url = article.get("url", "")
                reason_source = article.get("source")
            else:
                title = summary["tag"]
                url = ""
                reason_source = None

            ranked.append(
                {
                    "article_id": article_id,
                    "title": title,
                    "url": url,
                    "score": round(score, 3),
                    "reason": ", ".join(
                        filter(
                            None,
                            [
                                *reasons,
                                f"Source: {reason_source}" if reason_source else None,
                            ],
                        )
                    ),
                }
            )

    ranked.sort(key=lambda record: record["score"], reverse=True)
    return {"ranked_stories": ranked}

