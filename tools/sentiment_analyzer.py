from __future__ import annotations

from typing import Dict, List

from newsroom import Passage, SentimentScore

_POSITIVE_CUES = {"improved", "expanding", "better", "engaged", "helps", "support"}
_NEGATIVE_CUES = {"concern", "risk", "problem", "delay"}


def analyze_sentiment(passages: List[Passage]) -> Dict[str, List[SentimentScore]]:
    """Analyze sentiment and stance of passages using a keyword lexicon."""

    scores: List[SentimentScore] = []

    for passage in passages:
        text_lower = passage["text"].lower()
        positive = sum(1 for cue in _POSITIVE_CUES if cue in text_lower)
        negative = sum(1 for cue in _NEGATIVE_CUES if cue in text_lower)
        delta = positive - negative

        if delta > 0:
            sentiment = "positive"
            stance = "supportive"
        elif delta < 0:
            sentiment = "negative"
            stance = "critical"
        else:
            sentiment = "neutral"
            stance = "neutral"

        scores.append(
            {
                "passage_id": passage["id"],
                "sentiment": sentiment,
                "stance": stance,
                "score": float(delta),
            }
        )

    return {"sentiment_scores": scores}
