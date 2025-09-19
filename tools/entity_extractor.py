from __future__ import annotations

import sys
from typing import Dict, List, Optional

from newsroom import EntityMention, Passage
from newsroom.llm import extract_entities_with_llm

_KNOWN_ENTITIES = {
    "OpenAI": "ORG",
    "New York City": "LOCATION",
    "Metro Climate Desk": "ORG",
    "Brooklyn": "LOCATION",
    "Queens": "LOCATION",
    "Jamie Rivera": "PERSON",
    "Priya Das": "PERSON",
}


def _rule_based_entities(passages: List[Passage]) -> List[EntityMention]:
    mentions: List[EntityMention] = []
    for passage in passages:
        text = passage["text"]
        for entity, entity_type in _KNOWN_ENTITIES.items():
            if entity in text:
                mentions.append(
                    {
                        "span": entity,
                        "type": entity_type,
                        "passage_id": passage["id"],
                        "article_id": passage["article_id"],
                        "context": text,
                    }
                )
    return mentions


def extract_entities(
    passages: List[Passage],
    llm_mode: bool = False,
    embeddings: bool = False,
    model: Optional[str] = None,
    fallback_on_error: bool = True,
) -> Dict[str, List[EntityMention]]:
    """Identify named entities in passages with optional LLM support."""

    if llm_mode:
        try:
            llm_entities = extract_entities_with_llm(passages, model=model)
        except RuntimeError as exc:
            if not fallback_on_error:
                raise
            print(f"[newsroom] llm entity extraction fallback: {exc}", file=sys.stderr)
        else:
            return {"entities": llm_entities}  # type: ignore[return-value]

    mentions = _rule_based_entities(passages)
    return {"entities": mentions}
