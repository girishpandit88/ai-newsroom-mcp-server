from __future__ import annotations

from mcp.server.fastmcp import FastMCP

# Import all tool modules
from tools.fetcher import fetch_articles
from tools.passage_extractor import extract_passages
from tools.entity_extractor import extract_entities
from tools.disambiguator import disambiguate_entities
from tools.tagger import tag_entities
from tools.topic_classifier import classify_topic
from tools.sentiment_analyzer import analyze_sentiment
from tools.tag_summarizer import summarize_tags
from tools.fact_checker import fact_check
from tools.ranker import rank_stories
from tools.compiler import compile_digest
from tools.deliverer import deliver_digest

from resources.user_profile_store import get_user_profile

INSTRUCTIONS = (
    "This MCP server demonstrates an end-to-end newsroom workflow. "
    "Start by calling the 'fetch_articles' tool with source='sample' to load demo "
    "content, then move the data through passage extraction, entity work, "
    "classification, ranking, and digest delivery. Set NEWSROOM_USE_LLM=true (with an "
    "OPENAI_API_KEY) to route select steps through ChatGPT."
)

mcp = FastMCP("newsroom-server", instructions=INSTRUCTIONS)

# Register tools
mcp.tool()(fetch_articles)
mcp.tool()(extract_passages)
mcp.tool()(extract_entities)
mcp.tool()(disambiguate_entities)
mcp.tool()(tag_entities)
mcp.tool()(classify_topic)
mcp.tool()(analyze_sentiment)
mcp.tool()(summarize_tags)
mcp.tool()(fact_check)
mcp.tool()(rank_stories)
mcp.tool()(compile_digest)
mcp.tool()(deliver_digest)


@mcp.resource("user_profile://{user_id}")
def user_profile(user_id: str):
    """Return a demo user profile that powers the ranking step."""

    return get_user_profile(user_id)


if __name__ == "__main__":
    mcp.run(transport="stdio")
