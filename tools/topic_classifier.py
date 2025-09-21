from __future__ import annotations

import sys
from typing import Dict, List, Optional

from newsroom import Passage, TopicPrediction
from newsroom.llm import classify_topics_with_llm

_TOPIC_KEYWORDS = {
    "Technology": ["ai", "automation", "toolkit", "openai"],
    "Climate": ["climate", "air quality", "sensors"],
    "Civic": ["community", "policymakers", "residents"],
}


def classify_topic(
    passages: List[Passage],
    llm_mode: bool = False,
    model: Optional[str] = None,
    fallback_on_error: bool = True,
) -> Dict[str, List[TopicPrediction]]:
    """Classify passages into newsroom beats with optional LLM assistance."""

    if llm_mode and passages:
        try:
            llm_topics = classify_topics_with_llm(passages, model=model)
        except RuntimeError as exc:
            if not fallback_on_error:
                raise
            print(f"[newsroom] llm topic classification fallback: {exc}", file=sys.stderr)
        else:
            return {"topics": llm_topics}  # type: ignore[return-value]

    topics: List[TopicPrediction] = []

    for passage in passages:
        text_lower = passage["text"].lower()
        topic = "General"
        confidence = 0.5
        for candidate, keywords in _TOPIC_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                topic = candidate
                confidence = 0.9
                break
        topics.append(
            {
                "passage_id": passage["id"],
                "topic": topic,
                "confidence": confidence,
            }
        )

    return {"topics": topics}
