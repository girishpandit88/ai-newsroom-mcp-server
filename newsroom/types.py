from __future__ import annotations

from typing import List, Literal, TypedDict


class Article(TypedDict):
    """News article fetched from an upstream source."""

    id: str
    source: str
    title: str
    url: str
    timestamp: str
    author: str
    content: str


class Passage(TypedDict):
    """A snippet of an article that downstream tools can analyse."""

    id: str
    article_id: str
    order: int
    text: str


class EntityMention(TypedDict):
    """A raw entity span detected in a passage."""

    span: str
    type: Literal["PERSON", "ORG", "LOCATION", "OTHER"]
    passage_id: str
    article_id: str
    context: str


class ResolvedEntity(TypedDict):
    """A mention linked to a canonical identifier."""

    span: str
    canonical_id: str
    confidence: float
    type: Literal["PERSON", "ORG", "LOCATION", "OTHER"]
    passage_id: str
    article_id: str


class TaggedEntity(TypedDict):
    """Entity annotated with a newsroom specific category."""

    entity: str
    canonical_id: str
    category: str
    passage_id: str
    article_id: str


class TagSummary(TypedDict):
    """Aggregated summary for a given entity tag."""

    tag: str
    canonical_id: str
    category: str
    highlights: List[str]
    article_ids: List[str]


class TopicPrediction(TypedDict):
    """Topic classification for a passage."""

    passage_id: str
    topic: str
    confidence: float


class SentimentScore(TypedDict):
    """Sentiment and stance analysis result."""

    passage_id: str
    sentiment: Literal["positive", "neutral", "negative"]
    stance: Literal["supportive", "neutral", "critical"]
    score: float


class RankedStory(TypedDict):
    """Ranked story record ready for compilation into a digest."""

    article_id: str
    title: str
    url: str
    score: float
    reason: str
