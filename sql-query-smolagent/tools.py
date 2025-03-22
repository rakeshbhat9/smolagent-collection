from smolagents import tool
import os
from sqlalchemy import create_engine, text, inspect
import pandas as pd

#----------------------------------------------------------------------------------------------------------

def get_db_engine():
    """Create and return a new database engine instance"""
    pg_params = {
        'database': os.getenv('PG_DATABASE'),
        'user': os.getenv('PG_USER'),
        'password': os.getenv('PG_PASSWORD'),
        'host': os.getenv('PG_HOST'),
        'port': os.getenv('PG_PORT')
    }
    return create_engine(
        f"postgresql://{pg_params['user']}:{pg_params['password']}@{pg_params['host']}:{pg_params['port']}/{pg_params['database']}"
    )

#----------------------------------------------------------------------------------------------------------

def get_table_descriptions():
    """Get table descriptions for the prompt"""
    engine = get_db_engine()
    inspector = inspect(engine)
    table_descriptions = []
    for table_name in ['inventory', 'sales', 'expenses']:
        columns_info = [(col['name'], col['type']) for col in inspector.get_columns(table_name)]
        table_descriptions.append(f"{table_name} table:\n" + "\n".join(f"  - {col[0]}: {col[1]}" for col in columns_info))
    engine.dispose()
    return table_descriptions

#----------------------------------------------------------------------------------------------------------

@tool
def query_database(query: str) -> pd.DataFrame:
    """
    Execute a SQL query on the database and return the results as a pandas DataFrame.
    
    Args:
        query: SQL query to execute using pd.read_sql. The code should create a pandas DataFrame with the results.
             
    Returns:
        pd.DataFrame: Results of the query as a pandas DataFrame
    
    Example:
        query = "SELECT * FROM sales WHERE date >= current_date - interval '1 month'"
        df = query_database(query)
        return df
    """
    try:
        engine = get_db_engine()
        result_df = pd.read_sql(text(query), engine)
        engine.dispose()
        return result_df.to_dict(orient='records')
    except Exception as e:
        raise Exception(f"Error executing code: {str(e)}")
    
#----------------------------------------------------------------------------------------------------------