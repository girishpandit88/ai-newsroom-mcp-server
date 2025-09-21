from __future__ import annotations

import sys
from typing import Dict, List, Optional

from newsroom import ResolvedEntity, TaggedEntity
from newsroom.llm import tag_entities_with_llm

_CATEGORY_BY_TYPE = {
    "PERSON": "beat:people",
    "ORG": "beat:institutions",
    "LOCATION": "beat:places",
    "OTHER": "beat:general",
}


def tag_entities(
    resolved_entities: List[ResolvedEntity],
    llm_mode: bool = False,
    model: Optional[str] = None,
    fallback_on_error: bool = True,
) -> Dict[str, List[TaggedEntity]]:
    """Assign newsroom-specific categories to entities."""

    if llm_mode and resolved_entities:
        try:
            llm_tags = tag_entities_with_llm(resolved_entities, model=model)
        except RuntimeError as exc:
            if not fallback_on_error:
                raise
            print(f"[newsroom] llm tagging fallback: {exc}", file=sys.stderr)
        else:
            return {"tagged_entities": llm_tags}  # type: ignore[return-value]

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
