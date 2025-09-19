from __future__ import annotations

import os
from pprint import pprint

from resources.user_profile_store import get_user_profile
from tools.compiler import compile_digest
from tools.deliverer import deliver_digest
from tools.disambiguator import disambiguate_entities
from tools.entity_extractor import extract_entities
from tools.fact_checker import fact_check
from tools.fetcher import fetch_articles
from tools.passage_extractor import extract_passages
from tools.ranker import rank_stories
from tools.sentiment_analyzer import analyze_sentiment
from tools.tag_summarizer import summarize_tags
from tools.tagger import tag_entities
from tools.topic_classifier import classify_topic


def run_demo() -> None:
    """Run the newsroom pipeline locally so it is easy to validate."""

    llm_enabled = os.getenv("NEWSROOM_USE_LLM", "false").lower() in {"1", "true", "yes"}
    profile = get_user_profile("demo-user")

    try:
        fetched = fetch_articles(source="http://rss.cnn.com/rss/cnn_topstories.rss", limit=3)
    except Exception:
        fetched = fetch_articles(source="sample", limit=2)
    articles = fetched["articles"]

    all_passages = []
    for article in articles:
        passages = extract_passages(article_id=article["id"], content=article["content"])
        all_passages.extend(passages["passages"])

    entities = extract_entities(all_passages, llm_mode=llm_enabled)
    resolved = disambiguate_entities(
        entities["entities"],
        context="newsroom demo",
        llm_mode=llm_enabled,
    )
    tagged = tag_entities(resolved["resolved_entities"])

    topics = classify_topic(all_passages)
    sentiments = analyze_sentiment(all_passages)

    summaries = summarize_tags(
        tagged["tagged_entities"],
        all_passages,
        llm_mode=llm_enabled,
    )

    claims = [f"{article['title']} was announced" for article in articles]
    fact_checks = fact_check(claims, llm_mode=llm_enabled)

    ranked = rank_stories(profile, summaries["tag_summaries"], articles)
    digest = compile_digest(ranked["ranked_summaries"])
    delivery = deliver_digest(digest["digest"], delivery_channel="email", user_id=profile["user_id"])

    pprint(
        {
            "articles": articles,
            "passages": all_passages,
            "entities": entities,
            "resolved": resolved,
            "tagged": tagged,
            "topics": topics,
            "sentiments": sentiments,
            "summaries": summaries,
            "fact_checks": fact_checks,
            "ranked": ranked,
            "digest": digest,
            "delivery": delivery,
        }
    )


if __name__ == "__main__":
    run_demo()
