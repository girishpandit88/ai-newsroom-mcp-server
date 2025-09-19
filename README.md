# Newsroom MCP Server

![](./img/ai_news.jpg)


This repository contains a fully deterministic Model Context Protocol (MCP) server that
simulates a local newsroom workflow. The goal is to showcase how a client can orchestrate
article ingestion, entity analysis, fact checking, ranking, and digest delivery using a
chain of MCP tools without relying on third-party APIs.

## What's Included
- Sample article corpora in `resources/sample_articles.json`
- A suite of lightweight tools in `tools/` that implement each newsroom stage
- Typed models in `newsroom/types.py` so the generated tool schemas stay informative
- A `server.py` entrypoint that registers the tools with `FastMCP`
- A `main.py` helper that runs the entire pipeline locally for verification

## Quickstart
1. Install dependencies (the project uses [uv](https://github.com/astral-sh/uv)):
   ```bash
   uv sync
   ```
2. Run the local demo pipeline and inspect its output:
   ```bash
   uv run python main.py
   ```
   The script prints every intermediate payload so you can see how data flows from
   article fetches to a compiled digest.

> **Live sources** — `fetch_articles` now supports RSS URLs (for example,
> `https://rss.cnn.com/rss/cnn_topstories.rss`) when the server has outbound network
> access. The call automatically falls back to the canned dataset when you pass a
> named source such as `"sample"`.

## Running the MCP Server
You can bring the tools into any MCP-compatible client. Two handy options during
development are:

- Using the MCP CLI:
  ```bash
  uv run mcp dev ./server.py
  ```
  The CLI prints the JSON messages exchanged over stdio and is useful for debugging.

- Embedding the server in an MCP-aware IDE/agent:
  point the client at `python server.py` (or the equivalent `uv run python server.py`)
  and it will speak MCP over stdio.

## Recommended Tool Flow
While the tools are designed to be composable, the example workflow below mirrors the
logic in `main.py`:
1. `fetch_articles(source="sample")`
2. `extract_passages(article_id, content)` for each article
3. `extract_entities(passages)`
4. `disambiguate_entities(entities)`
5. `tag_entities(resolved_entities)`
6. `classify_topic(passages)` and `analyze_sentiment(passages)` as needed
7. `summarize_tags(tagged_entities, passages)`
8. `fact_check(claims)` (optional)
9. `rank_stories(user_profile, tag_summaries, articles)`
10. `compile_digest(ranked_summaries, format="markdown")`
11. `deliver_digest(digest, delivery_channel, user_id)`

Each tool returns structured JSON so downstream steps can consume the results directly.

## Enabling LLM-Backed Steps
Several tools can optionally call ChatGPT for richer reasoning. To enable this path:

1. Export your OpenAI key (`export OPENAI_API_KEY=sk-...`).
2. Optionally pick a model with `NEWSROOM_OPENAI_MODEL` (defaults to `gpt-4o-mini`).
3. Toggle the LLM-aware tools by setting `NEWSROOM_USE_LLM=true` before running the
   demo or starting the server.

When the environment variables are missing the pipeline stays fully deterministic and
uses the rule-based fallbacks outlined in `newsroom/llm.py`.

## Testing Changes
The quickest way to validate modifications is to run `uv run python main.py` after your
changes. Because the dataset is static, the output should remain deterministic unless you
intentionally alter the business logic.

## Next Steps
- Swap `resources/sample_articles.json` with feeds from your CMS
- Extend the keyword lists or plug in an LLM for richer analysis
- Wire the delivery tool to your messaging stack once you are ready for real side effects
