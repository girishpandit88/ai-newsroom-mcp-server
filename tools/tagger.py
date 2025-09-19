from __future__ import annotations

from typing import Dict, List

from newsroom import ResolvedEntity, TaggedEntity

_CATEGORY_BY_TYPE = {
    "PERSON": "beat:people",
    "ORG": "beat:institutions",
    "LOCATION": "beat:places",
    "OTHER": "beat:general",
}


def tag_entities(resolved_entities: List[ResolvedEntity]) -> Dict[str, List[TaggedEntity]]:
    """Assign newsroom-specific categories to entities."""

    tagged: List[TaggedEntity] = []
    for entity in resolved_entities:
        category = _CATEGORY_BY_TYPE.get(entity["type"], "beat:general")
        tagged.append(
            {
                "entity": entity["span"],
                "canonical_id": entity["canonical_id"],
                "category": category,
                "passage_id": entity["passage_id"],
                "article_id": entity["article_id"],
            }
        )

    return {"tagged_entities": tagged}
