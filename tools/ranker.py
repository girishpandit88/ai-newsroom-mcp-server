from __future__ import annotations

from typing import Dict, List, Optional

from newsroom import Article, RankedStory, TagSummary


def rank_stories(
    user_profile: Dict,
    summaries: List[TagSummary],
    articles: Optional[List[Article]] = None,
) -> Dict[str, List[RankedStory]]:
    """Rank and personalise stories based on the user's interests."""

    preferred_topics = {topic.lower() for topic in user_profile.get("preferred_topics", [])}
    blocked_sources = {source.lower() for source in user_profile.get("blocked_sources", [])}
    article_lookup = {article["id"]: article for article in articles or []}

    ranked: List[RankedStory] = []
    for summary in summaries:
        article_ids = [article_id for article_id in summary["article_ids"] if article_id]
        for article_id in article_ids:
            article = article_lookup.get(article_id)
            if article and article["source"].lower() in blocked_sources:
                continue

            score = 1.0
            reason_parts = [f"Entity: {summary['tag']}"]
            if any(topic in summary["category"].lower() for topic in preferred_topics):
                score += 1.0
                reason_parts.append("Matches preferred topic")

            title = summary["tag"]
            url = ""
            if article:
                title = article["title"]
                url = article["url"]
                reason_parts.append(f"Source: {article['source']}")

            ranked.append(
                {
                    "article_id": article_id,
                    "title": title,
                    "url": url,
                    "score": score,
                    "reason": ", ".join(reason_parts),
                }
            )

    ranked.sort(key=lambda record: record["score"], reverse=True)
    return {"ranked_summaries": ranked}
