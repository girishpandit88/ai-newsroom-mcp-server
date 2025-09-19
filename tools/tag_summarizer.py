from __future__ import annotations

import sys
from typing import Dict, List, Optional

from newsroom import Passage, TagSummary, TaggedEntity
from newsroom.llm import summarize_tags_with_llm


def _build_highlight(text: str, limit: int = 160) -> str:
    words = text.split()
    highlight: List[str] = []
    length = 0

    for word in words:
        projected = length + (1 if highlight else 0) + len(word)
        if projected > limit:
            break
        highlight.append(word)
        length = projected

    snippet = " ".join(highlight)
    if snippet and len(snippet) < len(text):
        return f"{snippet}..."
    return snippet or text[:limit]


def summarize_tags(
    tags: List[TaggedEntity],
    passages: List[Passage],
    llm_mode: bool = False,
    model: Optional[str] = None,
    fallback_on_error: bool = True,
) -> Dict[str, List[TagSummary]]:
    """Generate structured summaries grouped by entity tags."""

    if llm_mode and tags:
        try:
            tag_summaries = summarize_tags_with_llm(tags, passages, model=model)
        except RuntimeError as exc:
            if not fallback_on_error:
                raise
            print(f"[newsroom] llm tag summarisation fallback: {exc}", file=sys.stderr)
        else:
            return {"tag_summaries": tag_summaries}  # type: ignore[return-value]

    passage_lookup = {passage["id"]: passage for passage in passages}
    summaries: Dict[str, TagSummary] = {}

    for tag in tags:
        passage = passage_lookup.get(tag["passage_id"])
        if not passage:
            continue

        summary = summaries.get(tag["canonical_id"])
        if not summary:
            summary = {
                "tag": tag["entity"],
                "canonical_id": tag["canonical_id"],
                "category": tag["category"],
                "highlights": [],
                "article_ids": [],
            }
            summaries[tag["canonical_id"]] = summary

        highlight = _build_highlight(passage["text"])
        if highlight:
            summary["highlights"].append(highlight)
        if tag["article_id"] not in summary["article_ids"]:
            summary["article_ids"].append(tag["article_id"])

    return {"tag_summaries": list(summaries.values())}
