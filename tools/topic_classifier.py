from __future__ import annotations

from typing import Dict, List

from newsroom import Passage, TopicPrediction

_TOPIC_KEYWORDS = {
    "Technology": ["ai", "automation", "toolkit", "openai"],
    "Climate": ["climate", "air quality", "sensors"],
    "Civic": ["community", "policymakers", "residents"],
}


def classify_topic(passages: List[Passage]) -> Dict[str, List[TopicPrediction]]:
    """Classify passages into newsroom beats using keyword heuristics."""

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
