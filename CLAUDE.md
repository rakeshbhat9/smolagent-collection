# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a collection of lightweight AI agents built using the `smolagents` framework. Each agent is self-contained within its own directory and designed for specific domain tasks. All agents follow a consistent architecture pattern using Streamlit for the UI and OpenRouter for LLM access.

## Repository Structure

The repository contains three independent agents:

- **eqs-smolagent/** - Equity reconciliation agent for asset management
- **yfinance-smolagent/** - Stock market data analysis agent
- **sql-query-smolagent/** - Natural language to SQL query agent for bookstore database

Each agent directory contains:
- `*-agent.py` - Main Streamlit application file
- `tools.py` - Custom tool definitions for the agent (except EQS which defines tools inline)
- `requirements.txt` - Python dependencies
- `README.md` - Agent-specific documentation

## Common Development Commands

### Running an Agent

Each agent uses Streamlit. Navigate to the specific agent directory and run:

```bash
cd <agent-directory>
streamlit run <agent-file>.py
```

Examples:
```bash
cd eqs-smolagent && streamlit run eqs-agent.py
cd yfinance-smolagent && streamlit run yfinance-agent.py
cd sql-query-smolagent && streamlit run bookstore-agent.py
```

### Installing Dependencies

Each agent has its own requirements file:

```bash
cd <agent-directory>
pip install -r requirements.txt
```

## Architecture Pattern

All agents follow a consistent architecture:

### 1. Tool Definition
Tools are defined using the `@tool` decorator from `smolagents`. Tools must:
- Have clear docstrings describing their purpose, args, and return values
- Return JSON-serializable data structures
- Handle errors gracefully

**Example from yfinance-smolagent/tools.py:**
```python
@tool
def get_company_info(stock: str) -> dict[str, dict]:
    """Docstring with Args and Returns..."""
    import yfinance as yf
    data = yf.Ticker(stock)
    return {
        "business_summary": data.info["longBusinessSummary"],
        "company_officers": data.info["companyOfficers"]
    }
```

### 2. Agent Configuration
Agents use `ToolCallingAgent` with:
- **Model**: OpenAIServerModel pointing to OpenRouter API
- **Tools**: List of tool functions
- **Prompt Templates**: Custom system prompts that guide agent behavior

**Key prompt template structure:**
```python
prompt_templates = {
    "system_prompt": "...",  # Main instructions for the agent
    "planning": {...},       # Planning phase templates
    "managed_agent": {...},  # Sub-agent templates
    "final_answer": {...}    # Final response templates
}
```

### 3. Streamlit UI Pattern
All agents follow this UI structure:
- Model selection dropdown (yfinance and sql-query agents)
- Chat history stored in `st.session_state.chat_history`
- Example queries in sidebar
- Chat interface using `st.chat_input()` and `st.chat_message()`
- Error handling with `st.error()`
- Loading states with `st.spinner()`

### 4. Environment Configuration
All agents require a `.env` file in their directory:

- **eqs-smolagent** and **yfinance-smolagent**: `OPENROUTER_API_KEY`
- **sql-query-smolagent**: `OPENROUTER_API_KEY`, `PG_DATABASE`, `PG_USER`, `PG_PASSWORD`, `PG_HOST`, `PG_PORT`

## Agent-Specific Details

### EQS Reconciliation Agent
- **Purpose**: Reconcile equity breaks between calculated and reported values
- **Data Source**: CSV files in `data/` folder (`trade_activity.csv`, `positions.csv`, `total_equity.csv`)
- **Tools Defined**: Inline in `eqs-agent.py` (not in separate tools.py)
- **Key Tools**: `list_securities()`, `security_valuation()`, `security_trades()`, `equity_breakdown()`, `analyze_price_impact()`
- **Model**: Uses `deepseek/deepseek-chat-v3.1` via OpenRouter

### YFinance Agent
- **Purpose**: Financial analysis using Yahoo Finance data
- **Tools Location**: `yfinance-smolagent/tools.py`
- **Key Tools**: `get_company_info()`, `get_company_financials()`, `get_company_news()`
- **Special Handling**: Includes timestamp conversion logic (`convert_timestamps_to_strings()`) to ensure JSON serializability
- **Phoenix Integration**: Uses Phoenix OTEL for tracing with `register(project_name="yfinance-agent", auto_instrument=True)`

### SQL Query Agent
- **Purpose**: Natural language querying of PostgreSQL bookstore database
- **Tools Location**: `sql-query-smolagent/tools.py`
- **Key Tools**: `query_database()`, `get_table_descriptions()`
- **Database**: PostgreSQL with tables: `inventory`, `sales`, `expenses`
- **Special Pattern**: Database schema is dynamically injected into system prompt
- **Phoenix Integration**: Uses Phoenix OTEL for tracing with `register(project_name="bookstore-agent", auto_instrument=True)`

## Key Implementation Patterns

### Adding a New Tool
1. Define the tool function with `@tool` decorator in `tools.py` (or inline in agent file)
2. Add comprehensive docstring with Args and Returns
3. Import tool in main agent file
4. Add to agent's tools list: `agent = ToolCallingAgent(tools=[...], ...)`
5. Update system prompt to explain when/how to use the new tool

### Modifying System Prompts
System prompts are crucial for agent behavior. They should:
- Define the agent's role and expertise
- List available tools and when to use them
- Specify output format requirements (markdown tables, headers, etc.)
- Include domain-specific analysis steps
- Be stored in `prompt_templates["system_prompt"]`

### Data Serialization
When tools return complex data types (pandas DataFrames, Timestamps):
- Convert to JSON-serializable formats
- Use helper functions like `convert_timestamps_to_strings()` (see yfinance/tools.py)
- Return dictionaries or lists of dictionaries
- sql-query-smolagent returns `df.to_dict(orient='records')`

### Session State Management
Streamlit session state pattern used across all agents:
```python
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# After agent response:
st.session_state.chat_history.append((query, response))
```

## Testing Agents

While there are no formal test files, you can verify agent functionality by:
1. Running the Streamlit app
2. Using example queries from the sidebar
3. Verifying tool outputs are correctly formatted
4. Checking error handling with invalid inputs

## Dependencies

Common across all agents:
- `smolagents==1.8.0`
- `streamlit` (1.42.0 for eqs and yfinance)
- `pandas`
- `openai` (1.61.1 for eqs and yfinance)

Agent-specific:
- **yfinance-smolagent**: `yfinance==0.2.52`
- **sql-query-smolagent**: `sqlalchemy`, `psycopg2-binary`, `python-dotenv`
- **eqs-smolagent**: No additional domain-specific dependencies

## OpenRouter Integration

All agents use OpenRouter as the LLM backend via `OpenAIServerModel`:
```python
model = OpenAIServerModel(
    model_id="model_name",
    api_base="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)
```

Available models vary by agent:
- yfinance: `openai/gpt-5-mini`, `openai/gpt-4.1-nano`
- sql-query: `openai/gpt-4.1-nano`
- eqs: `deepseek/deepseek-chat-v3.1`
