from smolagents import tool
import json
import pandas as pd

#----------------------------------------------------------------------------------
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
    
    data_dict = {
        "business_summary": data.info["longBusinessSummary"],
        "company_officers": data.info["companyOfficers"]
    }
    
    return data_dict

#----------------------------------------------------------------------------------

def convert_timestamps_to_strings(obj):
    """Recursively convert pandas Timestamps to strings in nested data structures."""
    if isinstance(obj, pd.Timestamp):
        return obj.strftime('%Y-%m-%d')
    elif isinstance(obj, dict):
        return {str(k) if isinstance(k, pd.Timestamp) else k: convert_timestamps_to_strings(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_timestamps_to_strings(item) for item in obj]
    elif pd.isna(obj):
        return None
    elif isinstance(obj, (pd.Series, pd.DataFrame)):
        # Convert pandas objects to dict and then process
        return convert_timestamps_to_strings(obj.to_dict())
    else:
        return obj

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
    
    try:
        data = yf.Ticker(stock)
        
        # Get raw data
        raw_data = {
            "income_statement": data.get_income_stmt(as_dict=True, pretty=True),
            "balance_sheet": data.get_balance_sheet(as_dict=True, pretty=True),
            "cash_flow": data.get_cashflow(as_dict=True, pretty=True),
            "analyst_price_target": data.get_analyst_price_targets(),
            "earnings_estimate": data.get_earnings_estimate(as_dict=True),
        }
        
        # Convert all timestamps to strings to make it JSON serializable
        data_dict = convert_timestamps_to_strings(raw_data)
        
        # Test if the data is JSON serializable
        try:
            json.dumps(data_dict)
        except (TypeError, ValueError) as e:
            print(f"Serialization test failed: {e}")
            # Return a simplified version if full data fails
            return {"error": f"Data serialization failed: {str(e)}", "stock": stock}
        
        return data_dict
        
    except Exception as e:
        print(f"Error in get_company_financials for {stock}: {e}")
        return {"error": str(e), "stock": stock}

#----------------------------------------------------------------------------------

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

#----------------------------------------------------------------------------------