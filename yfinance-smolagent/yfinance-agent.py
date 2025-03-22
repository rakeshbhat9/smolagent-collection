from smolagents import (
    OpenAIServerModel,
    ToolCallingAgent,
    load_dotenv
)
from tools import get_company_info, get_company_financials, get_company_news
import os
load_dotenv()
import streamlit as st

#----------------------------------------------------------------------------------

# Initialize models
def get_model(model_name: str):
    if model_name == "Gemini 2.0":
        return OpenAIServerModel(
            model_id="gemini-2.0-flash-001",
            api_base="https://generativelanguage.googleapis.com/v1beta/openai/",    
            api_key=os.getenv("GEMINI_API_KEY"),
        )
    else:  # Mistral
        return OpenAIServerModel(
            model_id="mistral-small-latest",
            api_base="https://api.mistral.ai/v1",
            api_key=os.getenv("MISTRAL_API_KEY"),
        )

#----------------------------------------------------------------------------------

prompt = """
You are an experienced financial analyst. 

You have tools to get company information, latest news and all core financials given the stock symbol/s. 

Your job is to analyze the data provided by the tools and provide detailed insights as per the user's query.

#IMPORTANT:
- Always provide supporting numerical data along with your responses to make it easy for the user to digest the information.
- Please always return the data in markdown format so it's easier for the user to read.
"""
#----------------------------------------------------------------------------------

def main():
    # Streamlit UI
    st.title("🤖 Financial Analyst Agent 📈")
    
    # Model selection
    model_name = st.selectbox(
        "Select Language Model",
        ["Gemini 2.0", "Mistral"],
        index=0
    )
    
    # Initialize model and agent
    model = get_model(model_name)
    agent = ToolCallingAgent(
        tools=[get_company_info, get_company_financials, get_company_news],
        model=model,    
        prompt_templates={'system_prompt': prompt},
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

#----------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
