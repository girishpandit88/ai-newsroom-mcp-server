from __future__ import annotations

import sys
from typing import Dict, List, Optional

from newsroom import EntityMention, ResolvedEntity
from newsroom.llm import resolve_entities_with_llm

_CANONICAL_IDS = {
    "OpenAI": "Q12345",
    "New York City": "Q60",
    "Metro Climate Desk": "Q99901",
    "Brooklyn": "Q18426",
    "Queens": "Q60-Queens",
    "Jamie Rivera": "Q80001",
    "Priya Das": "Q80002",
}


def _rule_based_disambiguation(entities: List[EntityMention]) -> List[ResolvedEntity]:
    resolved: List[ResolvedEntity] = []
    for entity in entities:
        canonical_id = _CANONICAL_IDS.get(entity["span"], f"Q{abs(hash(entity['span'])) % 10000}")
        confidence = 0.95 if entity["span"] in _CANONICAL_IDS else 0.5
        resolved.append(
            {
                "span": entity["span"],
                "canonical_id": canonical_id,
                "confidence": confidence,
                "type": entity["type"],
                "passage_id": entity["passage_id"],
                "article_id": entity["article_id"],
            }
        )
    return resolved


def disambiguate_entities(
    entities: List[EntityMention],
    context: str = "",
    llm_mode: bool = False,
    model: Optional[str] = None,
    fallback_on_error: bool = True,
) -> Dict[str, List[ResolvedEntity]]:
    """Resolve ambiguous entities to canonical IDs with optional LLM assistance."""

    if llm_mode and entities:
        try:
            resolved_llm = resolve_entities_with_llm(entities, context=context, model=model)
        except RuntimeError as exc:
            if not fallback_on_error:
                raise
            print(f"[newsroom] llm disambiguation fallback: {exc}", file=sys.stderr)
        else:
            return {"resolved_entities": resolved_llm}  # type: ignore[return-value]

    resolved = _rule_based_disambiguation(entities)
    return {"resolved_entities": resolved}
