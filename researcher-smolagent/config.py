"""
Configuration for multi-agent research system.

Defines OpenRouter model configurations for:
- Researcher agent
- 3 Council review agents (methodology, comprehensiveness, clarity)
"""

import os
from smolagents import OpenAIServerModel
from dotenv import load_dotenv

load_dotenv()

# Model configurations for different agent roles
MODEL_CONFIGS = {
    "researcher": {
        "model_id": "google/gemini-2.0-flash-thinking-exp-01-21",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": os.getenv("OPENROUTER_API_KEY"),
        "description": "Strong reasoning and cost-effective for comprehensive research"
    },
    "council_methodology": {
        "model_id": "anthropic/claude-3.7-sonnet",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": os.getenv("OPENROUTER_API_KEY"),
        "description": "Excellent analytical assessment for methodological review"
    },
    "council_comprehensiveness": {
        "model_id": "google/gemini-2.0-flash-thinking-exp-01-21",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": os.getenv("OPENROUTER_API_KEY"),
        "description": "Good at holistic coverage assessment"
    },
    "council_clarity": {
        "model_id": "openai/gpt-4.1-turbo",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": os.getenv("OPENROUTER_API_KEY"),
        "description": "Strong language and communication assessment"
    }
}


def get_model(config_key: str) -> OpenAIServerModel:
    """
    Create and return a configured OpenAIServerModel for the specified agent role.

    Args:
        config_key (str): One of "researcher", "council_methodology",
                         "council_comprehensiveness", "council_clarity"

    Returns:
        OpenAIServerModel: Configured model instance

    Raises:
        KeyError: If config_key is not valid
        ValueError: If OPENROUTER_API_KEY is not set
    """
    if config_key not in MODEL_CONFIGS:
        raise KeyError(f"Invalid config_key: {config_key}. Must be one of {list(MODEL_CONFIGS.keys())}")

    config = MODEL_CONFIGS[config_key]

    if not config["api_key"]:
        raise ValueError(
            "OPENROUTER_API_KEY not found in environment. "
            "Please set it in your .env file."
        )

    return OpenAIServerModel(
        model_id=config["model_id"],
        api_base=config["api_base"],
        api_key=config["api_key"]
    )


def get_all_model_info() -> dict:
    """
    Get information about all configured models.

    Returns:
        dict: Model information for all agent roles
    """
    return {
        key: {
            "model_id": conf["model_id"],
            "description": conf["description"]
        }
        for key, conf in MODEL_CONFIGS.items()
    }
