import streamlit as st
import pandas as pd
from smolagents import tool, CodeAgent,load_dotenv,ToolCallingAgent
from smolagents import OpenAIServerModel  # or any other LLM backend you want

import os

load_dotenv()


# ======================================
# Streamlit UI
# ======================================
# st.title("EQS Reconciliation Assistant")

# st.markdown("Upload Trade Activity, Positions, and Total Equity CSV files")

# trade_file = st.file_uploader("Upload Trade Activity CSV", type="csv")
# pos_file = st.file_uploader("Upload Positions CSV", type="csv")
# eq_file = st.file_uploader("Upload Total Equity CSV", type="csv")

# if trade_file and pos_file and eq_file:
trade_activity = pd.read_csv('data/trade_activity.csv')
positions = pd.read_csv('data/positions.csv')
total_equity = pd.read_csv('data/total_equity.csv')

st.success("✅ Data loaded successfully!")

# Show previews
with st.expander("Preview Trade Activity"):
    st.dataframe(trade_activity)
with st.expander("Preview Positions"):
    st.dataframe(positions)
with st.expander("Preview Total Equity"):
    st.dataframe(total_equity)

# ======================================
# Define Tools (using uploaded data)
# ======================================

@tool
def list_securities() -> list:
    """
    Return all unique securities from Trade Activity and Positions datasets.
    
    Returns:
        list: A list of unique security names from both Trade Activity and Positions datasets.
    """
    ta_sec = set(trade_activity["Security"].unique())
    pos_sec = set(positions["Security"].unique())
    return list(ta_sec.union(pos_sec))

@tool
def security_valuation(security: str) -> dict:
    """
    For a given security, analyze position and price data for discrepancies.
    
    Args:
        security (str): The security identifier
        
    Returns:
        dict: Detailed analysis of position and price data
    """
    pos = positions[positions["Security"] == security]
    trades = trade_activity[trade_activity["Security"] == security]
    
    if pos.empty:
        return {"error": f"No position found for {security}"}

    row = pos.iloc[0]
    calc_value = row["Current Position"] * row["Market Price"]
    
    # Calculate average trade price
    if not trades.empty:
        last_trade = trades.iloc[-1]
        price_diff = row["Market Price"] - last_trade["Price"]
    else:
        price_diff = 0

    return {
        "Security": security,
        "Current Position": row["Current Position"],
        "Market Price": row["Market Price"],
        "Last Trade Price": last_trade["Price"] if not trades.empty else None,
        "Price Difference": price_diff,
        "Market Value (System)": row["Market Value"],
        "Market Value (Recalc)": calc_value,
        "Valuation Diff": calc_value - row["Market Value"],
        "Trade Count": len(trades)
    }

@tool
def security_trades(security: str) -> str:
    """
    Return all trades for a given security from the Trade Activity dataset.
    
    Args:
        security (str): The name or identifier of the security to get trades for.
        
    Returns:
        str: String representation of all trades for the security, or error message if none found.
    """
    trades = trade_activity[trade_activity["Security"] == security]
    if trades.empty:
        return f"No trades found for {security}"
    return trades.to_string(index=False)

@tool
def equity_breakdown() -> dict:
    """
    Return calculated vs reported equity breakdown and difference.
    
    Returns:
        dict: A dictionary containing:
            - 'Opening Equity' (float): Starting equity value
            - 'Trade P&L' (float): Profit/Loss from trades
            - 'Market Revaluation P&L' (float): Profit/Loss from market revaluation
            - 'Calculated Closing Equity' (float): Calculated closing equity
            - 'Reported Closing Equity' (float): Reported closing equity from system
            - 'Break' (float): Difference between calculated and reported equity
    """
    opening = total_equity.loc[0, "Opening Equity"]
    trade_pl = total_equity.loc[0, "Trade P&L"]
    market_pl = total_equity.loc[0, "Market Revaluation P&L"]
    reported = total_equity.loc[0, "Closing Equity (Reported)"]

    calc_equity = opening + trade_pl + market_pl

    return {
        "Opening Equity": opening,
        "Trade P&L": trade_pl,
        "Market Revaluation P&L": market_pl,
        "Calculated Closing Equity": calc_equity,
        "Reported Closing Equity": reported,
        "Break": calc_equity - reported,
    }

@tool
def analyze_price_impact(security: str) -> dict:
    """
    Analyze price impact on market value for a security.
    
    Args:
        security (str): The security identifier
        
    Returns:
        dict: Price impact analysis
    """
    pos = positions[positions["Security"] == security]
    trades = trade_activity[trade_activity["Security"] == security]
    
    if pos.empty:
        return {"error": f"No position found for {security}"}

    row = pos.iloc[0]
    if not trades.empty:
        last_trade = trades.iloc[-1]
        theoretical_value = row["Current Position"] * last_trade["Price"]
        reported_value = row["Market Value"]
        price_impact = reported_value - theoretical_value
        
        return {
            "Security": security,
            "System Price": row["Market Price"],
            "Last Trade Price": last_trade["Price"],
            "Position": row["Current Position"],
            "Theoretical Value": theoretical_value,
            "Reported Value": reported_value,
            "Price Impact": price_impact
        }
    return {"error": "No trades found"}

# ======================================
# Agent Setup
# ======================================

prompt_templates = {
    "system_prompt": """
    You are a precise reconciliation assistant for an Asset Management firm. Your task is to identify the source of differences between Calculated and Reported Closing Equity.

    Analysis Steps:
    1. First, check the overall equity break using equity_breakdown()
    2. Get all securities using list_securities()
    3. For each security:
       - Check security_valuation() for position and price discrepancies
       - Use analyze_price_impact() to quantify price-related issues
       - Review security_trades() for any trade-related impacts
    
    Focus Areas:
    - Price differences between trade price and system price
    - Position mismatches
    - Market value calculation discrepancies
    
    Provide:
    1. Total break amount and percentage
    2. Specific securities causing the break
    3. Root cause analysis (price/position/calculation issue)
    4. Clear recommendations for fixing the break
    """,
    "planning": {
        "initial_plan": "",
        "update_plan_pre_messages": "",
        "update_plan_post_messages": "",
    },
    "managed_agent": {"task": "", "report": ""},
    "final_answer": {"pre_messages": "", "post_messages": ""},
    }

model = OpenAIServerModel(
    model_id="deepseek/deepseek-chat-v3.1",
    api_base="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
tools = [list_securities, security_valuation, security_trades, equity_breakdown,analyze_price_impact]
agent = ToolCallingAgent(tools=tools, model=model,prompt_templates=prompt_templates, add_base_tools=True)

# ======================================
# User Query
# ======================================   

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
                # st.session_state.chat_history.append((query, response))
    except Exception as e:
        st.error(f"Error: {str(e)}")

#Please analyze the Total Equity break using Trade Activity and Positions. I need to explain difference between Closing Equity (Calc) & Closing Equity (Reported)