from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Sequence

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency
    OpenAI = None  # type: ignore[assignment]

PromptMessage = Dict[str, Any]


_DEFAULT_MODEL = os.getenv("NEWSROOM_OPENAI_MODEL", "gpt-4o-mini")
_LLM_UNAVAILABLE_ERR = "OpenAI client unavailable; set OPENAI_API_KEY to enable llm_mode"


def _message(role: str, text: str) -> PromptMessage:
    return {"role": role, "content": [{"type": "text", "text": text}]}


_PASSAGE_SYSTEM_PROMPT: List[PromptMessage] = [
    _message(
        "system",
        (
            "You split news articles into coherent passages for downstream tools. "
            "Return JSON with key 'passages'. The value must be a list where each item "
            "contains a 'text' field. Keep each passage focused and under the provided "
            "max_length in characters. Avoid overlapping content."
        ),
    )
]

_ENTITY_SYSTEM_PROMPT: List[PromptMessage] = [
    _message(
        "system",
        (
            "You are an information extraction assistant for a newsroom. Return JSON with "
            "a single key 'entities' whose value is a list. Each list item must be an object "
            "containing span, type (PERSON/ORG/LOCATION/OTHER), passage_id, article_id, and "
            "context (a short excerpt)."
        ),
    )
]

_TOPIC_SYSTEM_PROMPT: List[PromptMessage] = [
    _message(
        "system",
        (
            "You are a newsroom beat classifier. Categorise each news passage into one of the "
            "beats: Technology, Climate, Civic, or General (use General when unsure). Return "
            "JSON with key 'topics' whose value is a list of objects containing passage_id, "
            "topic, and confidence (0-1)."
        ),
    )
]

_DISAMBIGUATION_SYSTEM_PROMPT: List[PromptMessage] = [
    _message(
        "system",
        (
            "You are an entity linking assistant. Map entities to canonical identifiers. Return "
            "JSON with key 'resolved_entities' whose value is a list of objects. Each object must "
            "provide span, canonical_id, confidence (0-1), type, passage_id, and article_id."
        ),
    )
]

_TAG_SUMMARY_SYSTEM_PROMPT: List[PromptMessage] = [
    _message(
        "system",
        (
            "You are a newsroom summariser. Group information by entity tag and produce concise "
            "highlights. Return JSON with key 'tag_summaries', a list where each item has tag, "
            "canonical_id, category, highlights (list of strings), and article_ids (list of strings)."
        ),
    )
]

_TAGGING_SYSTEM_PROMPT: List[PromptMessage] = [
    _message(
        "system",
        (
            "You assign newsroom categories to canonicalised entities. Return JSON with key "
            "'tagged_entities'. Each item must include entity (original span), canonical_id, "
            "category, passage_id, and article_id. Use concise, consistent category labels."
        ),
    )
]

_FACT_CHECK_SYSTEM_PROMPT: List[PromptMessage] = [
    _message(
        "system",
        (
            "You are a fact-check assistant. Evaluate each claim and return JSON with key "
            "'checked_claims'. The list entries must contain claim, status (supported/contradicted/"
            "unverified), and references (list of {source,url})."
        ),
    )
]


def _client() -> Optional["OpenAI"]:
    if OpenAI is None:
        return None
    if not os.getenv("OPENAI_API_KEY"):
        return None
    return OpenAI()


def _call_json_response(
    messages: Sequence[PromptMessage],
    *,
    model: Optional[str] = None,
    temperature: float = 0.0,
) -> Dict[str, Any]:
    client = _client()
    if client is None:
        raise RuntimeError(_LLM_UNAVAILABLE_ERR)

    completion = client.chat.completions.create(
        model=model or _DEFAULT_MODEL,
        messages=list(messages),
        temperature=temperature,
        response_format={"type": "json_object"},
    )

    try:
        content = completion.choices[0].message.content or ""
    except (AttributeError, IndexError) as exc:  # pragma: no cover - defensive
        raise RuntimeError("Unexpected response format from OpenAI") from exc

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise RuntimeError("OpenAI response was not valid JSON") from exc


def _chunk_text(text: str, max_length: int) -> List[str]:
    words = text.split()
    if not words:
        return []

    chunks: List[str] = []
    current: List[str] = []
    current_len = 0

    for word in words:
        additional = len(word) + (1 if current else 0)
        if current_len + additional > max_length and current:
            chunks.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len += additional

    if current:
        chunks.append(" ".join(current))

    return chunks


def extract_passages_with_llm(
    article_id: str,
    content: str,
    max_length: int = 320,
    model: Optional[str] = None,
) -> List[Dict[str, Any]]:
    if not content.strip():
        return []

    messages: List[PromptMessage] = list(_PASSAGE_SYSTEM_PROMPT)
    messages.append(
        _message(
            "user",
            json.dumps(
                {
                    "article_id": article_id,
                    "max_length": max_length,
                    "content": content,
                }
            ),
        )
    )

    parsed = _call_json_response(messages, model=model)

    raw_passages = parsed.get("passages", [])
    if not isinstance(raw_passages, list):
        raise RuntimeError("LLM returned passages in unexpected format")

    passages: List[Dict[str, Any]] = []
    order = 0

    for raw in raw_passages:
        if isinstance(raw, dict):
            text = str(raw.get("text", "")).strip()
        elif isinstance(raw, str):
            text = raw.strip()
        else:
            continue

        if not text:
            continue

        for chunk in _chunk_text(text, max_length) or [text]:
            cleaned = chunk.strip()
            if not cleaned:
                continue
            order += 1
            passages.append(
                {
                    "id": f"{article_id}-p{order}",
                    "article_id": article_id,
                    "order": order,
                    "text": cleaned,
                }
            )

    return passages


def tag_entities_with_llm(
    resolved_entities: List[Dict[str, Any]],
    model: Optional[str] = None,
) -> List[Dict[str, Any]]:
    if not resolved_entities:
        return []

    messages: List[PromptMessage] = list(_TAGGING_SYSTEM_PROMPT)
    messages.append(
        _message("user", json.dumps({"resolved_entities": resolved_entities}))
    )

    parsed = _call_json_response(messages, model=model)
    tagged = parsed.get("tagged_entities", [])
    return [record for record in tagged if isinstance(record, dict)]


def extract_entities_with_llm(passages: List[Dict[str, Any]], model: Optional[str] = None) -> List[Dict[str, Any]]:
    messages: List[PromptMessage] = list(_ENTITY_SYSTEM_PROMPT)

    for passage in passages:
        messages.append(
            _message(
                "user",
                json.dumps(
                    {
                        "passage_id": passage.get("id", ""),
                        "article_id": passage.get("article_id", ""),
                        "text": passage.get("text", ""),
                    }
                ),
            )
        )

    parsed = _call_json_response(messages, model=model)
    entities = parsed.get("entities", [])
    return [entity for entity in entities if isinstance(entity, dict)]


def classify_topics_with_llm(
    passages: List[Dict[str, Any]],
    model: Optional[str] = None,
) -> List[Dict[str, Any]]:
    messages: List[PromptMessage] = list(_TOPIC_SYSTEM_PROMPT)

    for passage in passages:
        messages.append(
            _message(
                "user",
                json.dumps(
                    {
                        "passage_id": passage.get("id", ""),
                        "article_id": passage.get("article_id", ""),
                        "text": passage.get("text", ""),
                    }
                ),
            )
        )

    parsed = _call_json_response(messages, model=model)
    topics = parsed.get("topics", [])
    return [topic for topic in topics if isinstance(topic, dict)]


def resolve_entities_with_llm(
    entities: List[Dict[str, Any]],
    context: str,
    model: Optional[str] = None,
) -> List[Dict[str, Any]]:
    messages: List[PromptMessage] = list(_DISAMBIGUATION_SYSTEM_PROMPT)
    messages.append(_message("user", json.dumps({"context": context})))
    messages.append(_message("user", json.dumps({"entities": entities})))

    parsed = _call_json_response(messages, model=model)
    resolved = parsed.get("resolved_entities", [])
    return [record for record in resolved if isinstance(record, dict)]


def summarize_tags_with_llm(
    tags: List[Dict[str, Any]],
    passages: List[Dict[str, Any]],
    model: Optional[str] = None,
) -> List[Dict[str, Any]]:
    messages: List[PromptMessage] = list(_TAG_SUMMARY_SYSTEM_PROMPT)
    messages.append(_message("user", json.dumps({"tags": tags, "passages": passages})))

    parsed = _call_json_response(messages, model=model, temperature=0.2)
    summaries = parsed.get("tag_summaries", [])
    return [summary for summary in summaries if isinstance(summary, dict)]


def fact_check_with_llm(
    claims: List[str],
    model: Optional[str] = None,
) -> List[Dict[str, Any]]:
    messages: List[PromptMessage] = list(_FACT_CHECK_SYSTEM_PROMPT)
    messages.append(_message("user", json.dumps({"claims": claims})))

    parsed = _call_json_response(messages, model=model, temperature=0.1)
    checked = parsed.get("checked_claims", [])
    return [item for item in checked if isinstance(item, dict)]
