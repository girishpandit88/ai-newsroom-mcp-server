from __future__ import annotations

from typing import Dict, List

from newsroom import RankedStory


def compile_digest(
    ranked_summaries: List[RankedStory],
    format: str = "markdown",
) -> Dict[str, str]:
    """Format ranked summaries into a newsroom digest."""

    if format not in {"markdown", "text"}:
        raise ValueError("Only 'markdown' and 'text' are supported in the demo")

    lines: List[str] = []
    for story in ranked_summaries:
        title = story["title"]
        reason = story["reason"]
        score = f"score: {story['score']:.1f}"
        if format == "markdown" and story["url"]:
            lines.append(f"- [{title}]({story['url']}) — {reason} ({score})")
        else:
            url_part = f" {story['url']}" if story["url"] else ""
            lines.append(f"- {title}{url_part} — {reason} ({score})")

    digest = "\n".join(lines)
    return {"digest": digest, "format": format, "item_count": str(len(ranked_summaries))}
