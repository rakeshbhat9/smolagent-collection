from smolagents import (
    OpenAIServerModel,
    ToolCallingAgent,
    tool,
    load_dotenv
)

import os
load_dotenv()
import streamlit as st

# -------------------------------------------------------------

@tool
def get_company_info(stock: str) -> dict[str, dict]:
    """
    Fetches company information for a given stock symbol using yfinance.

    Args:
        stock: The stock symbol/ticker to look up (e.g., 'AAPL' for Apple Inc.)
            Must be a valid stock symbol on supported exchanges.

    Returns:
        dict: Dictionary containing:
            - business_summary (str): Company's long business description
            - company_officers (list): List of company officers/executives with their details

    Raises:
        ValueError: If the stock symbol is invalid or data cannot be retrieved
    """
    import yfinance as yf
    
    data = yf.Ticker(stock)
    
    # Remove the unnecessary set literals ({}) around the values
    data_dict = {
        "business_summary": data.info["longBusinessSummary"],
        "company_officers": data.info["companyOfficers"]
    }
    
    return data_dict

@tool
def get_company_financials(stock: str) -> dict[str, dict]:
    """
    This function retrieves various financial information including income statement,
    balance sheet, cash flow statement, analyst price targets, earnings estimates
    and latest news for a specified stock using the yfinance library.

    Args:
        stock: The stock symbol/ticker to look up (e.g., 'AAPL' for Apple Inc.)
            Must be a valid stock symbol on supported exchanges.
    
    Returns:
        dict: Dictionary containing:
            - Year: Dictionary of Company's income statement
    """
    import yfinance as yf
    
    data = yf.Ticker(stock)
    
    data_dict = {"income_staement":data.get_income_stmt(as_dict=True,pretty=True),
                 "balance_sheet":data.get_balance_sheet(as_dict=True,pretty=True),
                 "cash_flow":data.get_cashflow(as_dict=True,pretty=True),
                 "analyst_price_target":data.get_analyst_price_targets(),
                 "earnings_estimate":data.get_earnings_estimate(as_dict=True),
                 }

    return data_dict

@tool
def get_company_news(stock: str) -> dict[dict]:
    """Get financial data and news for a given stock symbol.
    
    Args:
        stock: The stock symbol (e.g. 'AAPL' for Apple Inc.)
    Returns:
        dict[dict]:
            - latest_news: Most recent news article about the company
    Example:
        >>> data = get_company_news('AAPL')
        >>> print(data['latest_news'])

    """
    import yfinance as yf
    
    data = yf.Ticker(stock)
    
    data_dict = {"latest_news":data.get_news()}

    return data_dict
# -------------------------------------------------------------


model = OpenAIServerModel(
    model_id="gemini-2.0-flash-001",
    api_base="https://generativelanguage.googleapis.com/v1beta/openai/",    
    api_key=os.getenv("GEMINI_API_KEY"),
)

prompt = """
You are an experienced financial analayst. 

You have tools to get company information, latest news and all core financials given the stock symbol/s. 

Your job is to analyze the data provided by the tools and provide detailed insights as per the user's query.

#IMPORTANT:
- Always provide supporting numerical data along with your responses to make it easy for the user to digest the inormation.
- Please always return the data in markdown format so it's easier for the user to read.

"""

agent = ToolCallingAgent(
    tools=[get_company_info,get_company_financials,get_company_news],
    model=model,    
    prompt_templates={'system_prompt':prompt},
)

# -------------------------------------------------------------

def main():
    # Streamlit UI
    st.title("🤖 Financial Analyst Agent 📈")
    
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
    
    # Chat input without the help parameter
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

if __name__ == "__main__":
    main()
