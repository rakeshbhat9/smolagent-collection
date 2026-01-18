"""
Researcher agent creation and configuration.

Creates the main research agent with all research tools.
"""

from smolagents import ToolCallingAgent
from config import get_model
from tools import (
    web_search,
    scrape_webpage,
    analyze_document,
    synthesize_data,
    track_citations
)
from prompts.researcher_prompts import RESEARCHER_PROMPT


def create_researcher_agent() -> ToolCallingAgent:
    """
    Create and configure the main researcher agent.

    Returns:
        ToolCallingAgent: Configured researcher agent with all research tools

    Tools included:
        - web_search: Search the web using DuckDuckGo
        - scrape_webpage: Extract content from webpages
        - analyze_document: Analyze PDFs and documents
        - synthesize_data: Aggregate information from multiple sources
        - track_citations: Extract and manage citations

    Model: google/gemini-2.0-flash-thinking-exp-01-21 (strong reasoning, cost-effective)
    """
    model = get_model("researcher")

    agent = ToolCallingAgent(
        tools=[
            web_search,
            scrape_webpage,
            analyze_document,
            synthesize_data,
            track_citations
        ],
        model=model,
        prompt_templates=RESEARCHER_PROMPT,
        max_tool_threads=1  # Sequential tool execution for reliability
    )

    return agent
