from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Sequence

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency
    OpenAI = None  # type: ignore[assignment]

_DEFAULT_MODEL = os.getenv("NEWSROOM_OPENAI_MODEL", "gpt-4o-mini")
_LLM_UNAVAILABLE_ERR = "OpenAI client unavailable; set OPENAI_API_KEY to enable llm_mode"


def _client() -> Optional["OpenAI"]:
    if OpenAI is None:
        return None
    if not os.getenv("OPENAI_API_KEY"):
        return None
    return OpenAI()


def _call_json_response(
    messages: Sequence[Dict[str, str]],
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


def extract_entities_with_llm(passages: List[Dict[str, Any]], model: Optional[str] = None) -> List[Dict[str, Any]]:
    messages: List[Dict[str, str]] = [
        {
            "role": "system",
            "content": (
                "You are an information extraction assistant for a newsroom. "
                "Return JSON with a single key 'entities' whose value is a list. Each list "
                "item must be an object containing span, type (PERSON/ORG/LOCATION/OTHER), "
                "passage_id, article_id, and context (a short excerpt)."
            ),
        }
    ]

    for passage in passages:
        messages.append(
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "passage_id": passage.get("id", ""),
                        "article_id": passage.get("article_id", ""),
                        "text": passage.get("text", ""),
                    }
                ),
            }
        )

    parsed = _call_json_response(messages, model=model)
    entities = parsed.get("entities", [])
    return [entity for entity in entities if isinstance(entity, dict)]


def resolve_entities_with_llm(
    entities: List[Dict[str, Any]],
    context: str,
    model: Optional[str] = None,
) -> List[Dict[str, Any]]:
    messages: List[Dict[str, str]] = [
        {
            "role": "system",
            "content": (
                "You are an entity linking assistant. Map entities to canonical identifiers. "
                "Return JSON with key 'resolved_entities' whose value is a list of objects. "
                "Each object must provide span, canonical_id, confidence (0-1), type, "
                "passage_id, and article_id."
            ),
        },
        {
            "role": "user",
            "content": json.dumps({"context": context}),
        },
        {
            "role": "user",
            "content": json.dumps({"entities": entities}),
        },
    ]

    parsed = _call_json_response(messages, model=model)
    resolved = parsed.get("resolved_entities", [])
    return [record for record in resolved if isinstance(record, dict)]


def summarize_tags_with_llm(
    tags: List[Dict[str, Any]],
    passages: List[Dict[str, Any]],
    model: Optional[str] = None,
) -> List[Dict[str, Any]]:
    messages: List[Dict[str, str]] = [
        {
            "role": "system",
            "content": (
                "You are a newsroom summariser. Group information by entity tag and produce "
                "concise highlights. Return JSON with key 'tag_summaries', a list where each "
                "item has tag, canonical_id, category, highlights (list of strings), and "
                "article_ids (list of strings)."
            ),
        },
        {
            "role": "user",
            "content": json.dumps({"tags": tags, "passages": passages}),
        },
    ]

    parsed = _call_json_response(messages, model=model, temperature=0.2)
    summaries = parsed.get("tag_summaries", [])
    return [summary for summary in summaries if isinstance(summary, dict)]


def fact_check_with_llm(
    claims: List[str],
    model: Optional[str] = None,
) -> List[Dict[str, Any]]:
    messages: List[Dict[str, str]] = [
        {
            "role": "system",
            "content": (
                "You are a fact-check assistant. Evaluate each claim and return JSON with "
                "key 'checked_claims'. The list entries must contain claim, status "
                "(supported/contradicted/unverified), and references (list of {source,url})."
            ),
        },
        {
            "role": "user",
            "content": json.dumps({"claims": claims}),
        },
    ]

    parsed = _call_json_response(messages, model=model, temperature=0.1)
    checked = parsed.get("checked_claims", [])
    return [item for item in checked if isinstance(item, dict)]
