from smolagents import OpenAIServerModel, ToolCallingAgent, load_dotenv
from tools import get_company_info, get_company_financials, get_company_news
import os

load_dotenv()
import streamlit as st

# ----------------------------------------------------------------------------------------------------------

from phoenix.otel import register

# configure the Phoenix tracer
tracer_provider = register(project_name="yfinance-agent", auto_instrument=True)

# ----------------------------------------------------------------------------------


# Initialize models
def get_model(model_name: str):
    return OpenAIServerModel(
        model_id=model_name,
        api_base="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )


# ----------------------------------------------------------------------------------

prompt_templates = {
    "system_prompt": """

You are a senior financial analyst specializing in discrete asset management.

You have access to three key tools: Use all three tools to provide comprehensive financial analysis and insights. 
But please try not to use the same tool more than once.

get_company_info - Retrieve comprehensive company profiles
get_company_financials - Obtain detailed financial statements and metrics
get_company_news - Access real-time news and earnings reports

Your responsibilities include:
- Conducting in-depth financial analysis of stock symbols
- Comparing companies across key metrics (market cap, P/E ratio, debt/equity)
- Analyzing news impact on stock performance
- Providing investment-grade insights for asset allocation decisions

Analysis requirements:
Always include quantitative data in markdown tables
Use bold headers for key financial metrics
Highlight material news events with timestamped annotations
Compare at least 3 major financial metrics across companies
Include risk assessment based on financial health indicators
Response format:

## Executive Summary
[Company Name] is a leading player in the [industry sector]. Our analysis reveals:
- [Key financial insight 1]
- [Key financial insight 2]
- [Key financial insight 3]

## Company Profile
### Overview
[Company profile summary from get_company_info tool]

### Financial Health
**Key Metrics:**
| Metric         | Value      | Trend     |
|----------------|------------|-----------|
| Market Cap     | $X         | ↑/↓ X%    |
| P/E Ratio      | 15.2       | ↑/↓ X%    |
| Debt/Equity    | 0.45       | ↑/↓ X%    |
| Earnings Growth| 8%         | ↑/↓ X%    |

### Risk Assessment
[Analysis of financial health indicators from get_company_financials tool]

## Financial Analysis
### Core Metrics Comparison
| Metric         | Company A | Company B | Company C |
|----------------|----------|----------|----------|
| Market Cap     | $X       | $Y       | $Z       |
| P/E Ratio      | 15.2     | 18.7     | 12.4     |
| Debt/Equity    | 0.45     | 0.62     | 0.31     |
| Earnings Growth| 8%       | 5%       | 12%      |

### News Impact Analysis
[Analysis of recent news events from get_company_news tool]

## Investment Recommendation
[Detailed recommendation based on analysis, including:
- Strategic positioning
- Risk vs. reward assessment
- Recommended position (buy/hold/sell)
- Stop-loss/limit orders]

## Visual Analysis
[Embedded charts for:
- Market cap trends
- Financial ratio comparisons
- News event timeline]

## Disclaimer
[Standard disclaimer text from firm's policy]
#IMPORTANT:

Always verify data freshness from all three tools
Cross-reference financial metrics with news events
Provide clear recommendations based on analytical findings
Use bold for key financial indicators and timestamps """,
"planning": {
    "initial_plan": "",
    "update_plan_pre_messages": "",
    "update_plan_post_messages": "",
},
"managed_agent": {"task": "", "report": ""},
"final_answer": {"pre_messages": "", "post_messages": ""},
}
# ----------------------------------------------------------------------------------


def main():
    # Streamlit UI
    st.title("🤖 Financial Analyst Agent 📈")

    # Model selection
    model_name = st.selectbox(
        "Select Language Model",
        ["openai/gpt-4.1-nano"],
        index=0,
    )

    # Initialize model and agent
    model = get_model(model_name)
    agent = ToolCallingAgent(
        tools=[get_company_info, get_company_financials, get_company_news],
        model=model,
        prompt_templates=prompt_templates,
        max_tool_threads=1,
    )

    # Initialize chat history in session state if it doesn't exist
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Add example queries in the sidebar
    st.sidebar.header("Example Questions")
    st.sidebar.markdown("""
    Try asking questions like:
    - Run an analysis on AAPL
    - Show me the latest news about TSLA
    - Compare the financials of MSFT and GOOGL
    - What are the key business metrics for AMZN?
    - Tell me about META's company officers
    """)

    # Display chat history
    for i, (query, response) in enumerate(st.session_state.chat_history):
        with st.chat_message("user"):
            st.write(query)
        with st.chat_message("assistant"):
            st.write(response)

    # Chat input
    query = st.chat_input("Ask me anything about stocks...")

    if query:
        with st.chat_message("user"):
            st.write(query)

        try:
            with st.chat_message("assistant"):
                with st.spinner("Sourcing data and generating report..."):
                    response = agent.run(query)
                    st.write(response)
                    # Add the Q&A pair to chat history
                    st.session_state.chat_history.append((query, response))
        except Exception as e:
            st.error(f"Error: {str(e)}")


# ----------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
