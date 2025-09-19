from __future__ import annotations

from typing import Dict, List

from newsroom import Passage


def _chunk_text(text: str, max_length: int) -> List[str]:
    words = text.split()
    if not words:
        return []

    chunks: List[str] = []
    current: List[str] = []
    current_len = 0

    for word in words:
        additional = len(word) + (1 if current else 0)
        if current_len + additional > max_length:
            chunks.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len += additional

    if current:
        chunks.append(" ".join(current))

    return chunks


def extract_passages(
    article_id: str,
    content: str,
    max_length: int = 320,
) -> Dict[str, List[Passage]]:
    """Split full article text into coherent passages.

    The helper keeps passages short enough for downstream tools while preserving the
    original order.
    """

    passages: List[Passage] = []
    order = 0

    paragraphs = [block.strip() for block in content.split("\n") if block.strip()]
    for paragraph in paragraphs:
        for chunk in _chunk_text(paragraph, max_length):
            order += 1
            passages.append(
                {
                    "id": f"{article_id}-p{order}",
                    "article_id": article_id,
                    "order": order,
                    "text": chunk,
                }
            )

    if not passages:
        passages.append(
            {
                "id": f"{article_id}-p1",
                "article_id": article_id,
                "order": 1,
                "text": content.strip(),
            }
        )

    return {"passages": passages}
