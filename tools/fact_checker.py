from __future__ import annotations

import sys
from typing import Dict, List, Optional

from newsroom.llm import fact_check_with_llm

_KNOWN_FACTS = {
    "newsroom automation toolkit": {
        "status": "supported",
        "references": [
            {
                "source": "Example Company Press Release",
                "url": "https://example.com/newsroom/openai-toolkit",
            }
        ],
    },
    "hyperlocal climate data": {
        "status": "supported",
        "references": [
            {
                "source": "Metro Climate Desk Announcement",
                "url": "https://example.com/newsroom/climate-desk",
            }
        ],
    },
}


def fact_check(
    claims: List[str],
    llm_mode: bool = False,
    model: Optional[str] = None,
    fallback_on_error: bool = True,
) -> Dict[str, List[Dict]]:
    """Verify claims with canned references suitable for the demo."""

    if llm_mode and claims:
        try:
            checked = fact_check_with_llm(claims, model=model)
        except RuntimeError as exc:
            if not fallback_on_error:
                raise
            print(f"[newsroom] llm fact-check fallback: {exc}", file=sys.stderr)
        else:
            return {"checked_claims": checked}

    checked = []
    for claim in claims:
        result = {"claim": claim, "status": "unverified", "references": []}
        lowered = claim.lower()
        for cue, verdict in _KNOWN_FACTS.items():
            if cue in lowered:
                result["status"] = verdict["status"]
                result["references"] = verdict["references"]
                break
        checked.append(result)

    return {"checked_claims": checked}
