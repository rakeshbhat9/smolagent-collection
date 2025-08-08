from smolagents import OpenAIServerModel, ToolCallingAgent, load_dotenv
from tools import query_database, get_table_descriptions
import os

load_dotenv()
import streamlit as st

# ----------------------------------------------------------------------------------------------------------

from phoenix.otel import register

# configure the Phoenix tracer
tracer_provider = register(project_name="bookstore-agent", auto_instrument=True)

# ----------------------------------------------------------------------------------------------------------


# Initialize models
def get_model(model_name: str):
    return OpenAIServerModel(
        model_id=model_name,
        api_base="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )


# ----------------------------------------------------------------------------------------------------------
# Get table descriptions for the prompt
table_descriptions = get_table_descriptions()

prompt_templates = {
    "system_prompt": f"""
You are an expert Python developer with deep knowledge of SQL and pandas. 

The database has the following tables:
{chr(10).join(table_descriptions)}

IMPORTANT:
- Write SQL queries to extract data from the database
- Use "query_database" tool to execute SQL queries on the database
- Using the output dataframe from the tool call, please provide detailed answer to the user's query
- Where data can be formatted in a tabular format, please do so to make it easier for the user to read
- All prices are in GBP (£)""",
    "planning": {
        "initial_plan": "",
        "update_plan_pre_messages": "",
        "update_plan_post_messages": "",
    },
    "managed_agent": {"task": "", "report": ""},
    "final_answer": {"pre_messages": "", "post_messages": ""},
}


# ----------------------------------------------------------------------------------------------------------


def main():
    st.title("📚 Bookstore Analytics Assistant")
    st.write("Ask questions about your bookstore's inventory, sales, and expenses!")

    # Model selection
    model_name = st.selectbox(
        "Select Language Model",
        ["openai/gpt-4.1-nano"],
        index=0,
    )

    # Initialize model and agent
    model = get_model(model_name)
    agent = ToolCallingAgent(
        model=model,
        tools=[query_database],
        prompt_templates=prompt_templates,        
    )

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


# ----------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
