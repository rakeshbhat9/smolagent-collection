from smolagents import (
    OpenAIServerModel,
    ToolCallingAgent,
    tool,
    load_dotenv
)
import os
load_dotenv()
import streamlit as st
from sqlalchemy import create_engine, text, inspect
import pandas as pd

# -------------------------------------------------------------

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

# -------------------------------------------------------------

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

# -------------------------------------------------------------

@tool
def query_database(query: str) -> pd.DataFrame:
    """
    Execute a SQL query on the database and return the results as a pandas DataFrame.
    
    Args:
        query: SQL query to execute using pd.read_sql.The code should create a pandas DataFrame with the results.
             
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

# -------------------------------------------------------------

# Initialize the model and agent
model = OpenAIServerModel(
    model_id="gemini-2.0-flash-001",
    api_base="https://generativelanguage.googleapis.com/v1beta/openai/",    
    api_key=os.getenv("GEMINI_API_KEY"),
)

# Get table descriptions for the prompt
table_descriptions = get_table_descriptions()


prompt = f"""
You are an expert Python developer with deep knowledge of SQL and pandas. 

The database has the following tables:
{chr(10).join(table_descriptions)}

IMPORTANT:
- Write SQL queries to extract data from the database.- 
- Use "query_database" tool to execute SQL queries on the database
- Using the output dataframe from the tool call, please provide detailed answer to the user's query.
- Where data can be formatted in a tabular format, please do so to make it easier for the user to read.
- All prices are in GBP (£).


"""

# -------------------------------------------------------------

# Initialize code agent
agent = ToolCallingAgent(
    model=model,
    tools=[query_database],
    prompt_templates={'system_prompt': prompt},
)

# -------------------------------------------------------------

def main():
    st.title("📚 Bookstore Analytics Assistant")
    st.write("Ask questions about your bookstore's inventory, sales, and expenses!")

    # Initialize chat history in session state if it doesn't exist
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Add example queries in the sidebar
    st.sidebar.header("Example Questions")
    st.sidebar.markdown("""
    Try asking questions like:
    - Show me the total sales for each month
    - What items are currently in stock?
    - What were our highest expenses last month?
    - Compare sales and expenses for last quarter
    - Which items are running low in inventory?
    """)
    
    # Display chat history
    for i, (query, response) in enumerate(st.session_state.chat_history):
        with st.chat_message("user"):
            st.write(query)
        with st.chat_message("assistant"):
            st.write(response)
    
    # Chat input
    query = st.chat_input("Ask me anything about your bookstore...")
    
    if query:
        with st.chat_message("user"):
            st.write(query)
            
        try:
            with st.chat_message("assistant"):
                with st.spinner("Analyzing data..."):
                    output = agent.run(query)
                    st.write(output)
                    # Add the Q&A pair to chat history
                    st.session_state.chat_history.append((query, output))
        except Exception as e:
            st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()