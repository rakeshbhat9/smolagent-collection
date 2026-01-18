"""
Council review agents creation and configuration.

Creates 3 independent review agents with different perspectives:
1. Methodological Rigor Expert (Dr. Sarah Chen)
2. Comprehensiveness Expert (Prof. James Rodriguez)
3. Clarity & Communication Expert (Dr. Emily Thompson)
"""

from smolagents import ToolCallingAgent
from config import get_model
from prompts.council_prompts import (
    METHODOLOGICAL_REVIEWER_PROMPT,
    COMPREHENSIVENESS_REVIEWER_PROMPT,
    CLARITY_REVIEWER_PROMPT
)


def create_council_agents() -> list:
    """
    Create and configure the 3 council review agents.

    Returns:
        list: List of 3 ToolCallingAgent instances:
            [0] = Methodological reviewer (Dr. Sarah Chen)
            [1] = Comprehensiveness reviewer (Prof. James Rodriguez)
            [2] = Clarity reviewer (Dr. Emily Thompson)

    Each agent uses a different model for diversity:
        - Methodology: anthropic/claude-3.7-sonnet (analytical assessment)
        - Comprehensiveness: google/gemini-2.0-flash-thinking-exp-01-21 (holistic)
        - Clarity: openai/gpt-4.1-turbo (communication assessment)
    """
    # Reviewer 1: Methodological Rigor (Dr. Sarah Chen)
    methodology_agent = ToolCallingAgent(
        tools=[],  # Council members don't need external tools
        model=get_model("council_methodology"),
        prompt_templates=METHODOLOGICAL_REVIEWER_PROMPT
    )

    # Reviewer 2: Comprehensiveness (Prof. James Rodriguez)
    comprehensiveness_agent = ToolCallingAgent(
        tools=[],
        model=get_model("council_comprehensiveness"),
        prompt_templates=COMPREHENSIVENESS_REVIEWER_PROMPT
    )

    # Reviewer 3: Clarity & Communication (Dr. Emily Thompson)
    clarity_agent = ToolCallingAgent(
        tools=[],
        model=get_model("council_clarity"),
        prompt_templates=CLARITY_REVIEWER_PROMPT
    )

    return [methodology_agent, comprehensiveness_agent, clarity_agent]


def get_reviewer_names() -> list:
    """
    Get the names of the council reviewers for display purposes.

    Returns:
        list: List of reviewer names with specialties
    """
    return [
        "Dr. Sarah Chen (Methodology)",
        "Prof. James Rodriguez (Comprehensiveness)",
        "Dr. Emily Thompson (Clarity)"
    ]
