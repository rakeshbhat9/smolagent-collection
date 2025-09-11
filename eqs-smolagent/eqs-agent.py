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
    For a given security, return current position, market price, and calculated market value.
    Useful for identifying mismatches between system and recalculated values.
    
    Args:
        security (str): The name or identifier of the security to analyze.
        
    Returns:
        dict: A dictionary containing:
            - 'Security' (str): The security name
            - 'Current Position' (float): Current position quantity
            - 'Market Price' (float): Current market price
            - 'Market Value (System)' (float): System-calculated market value
            - 'Market Value (Recalc)' (float): Recalculated market value
            - 'Valuation Diff' (float): Difference between recalculated and system values
            - 'error' (str): Error message if security not found
    """
    pos = positions[positions["Security"] == security]
    if pos.empty:
        return {"error": f"No position found for {security}"}

    row = pos.iloc[0]
    calc_value = row["Current Position"] * row["Market Price"]

    return {
        "Security": security,
        "Current Position": row["Current Position"],
        "Market Price": row["Market Price"],
        "Market Value (System)": row["Market Value"],
        "Market Value (Recalc)": calc_value,
        "Valuation Diff": calc_value - row["Market Value"]
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

# ======================================
# Agent Setup
# ======================================

prompt_templates = {
            "system_prompt": f"""
                You are a reconciliation assistant for an Asset Management firm.

                You are given three datasets:
                - **Total Equity data**: {total_equity}
                - **Trade Activity data**: {trade_activity}
                - **Positions data**: {positions}                

                Use the provided tools to:
                1. Call equity_breakdown() to find the overall break.
                2. Call list_securities() to get all securities.
                3. For each security, use security_valuation() to see if market value discrepancies exist.
                4. If needed, use security_trades() to check if trade impacts explain mismatches.
                5. At the end, provide:
                - Break Summary (calculated vs reported equity)
                - Underliers causing the issue
                - Likely root cause (e.g., pricing mismatch, missing trade, wrong position)
                - Suggested next steps for reconciliation team
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
tools = [list_securities, security_valuation, security_trades, equity_breakdown]
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