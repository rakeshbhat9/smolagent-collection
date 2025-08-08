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
    "system_prompt": """You are an experienced financial analyst. 

You have tools to get company information, latest news and all core financials given the stock symbol/s. 

Your job is to analyze the data provided by the tools and provide detailed insights as per the user's query.

#IMPORTANT:
- Always provide supporting numerical data along with your responses to make it easy for the user to digest the information.
- Please always return the data in markdown format so it's easier for the user to read.""",
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
