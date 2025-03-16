# SQL Query SmoLAgent
A specialized agent for querying and analyzing bookstore data using SQL and PostgreSQL database.

## Description
This repository contains a SmoLAgent implementation specifically designed to interact with a bookstore database. The agent can analyze inventory, sales, and expenses data through natural language queries, making it easier for users to get insights from their bookstore data.

## Features
- Natural language to SQL query conversion
- Analyze inventory status
- Track sales performance
- Monitor expenses
- Interactive Streamlit UI for easy querying
- Tabular data presentation

## Installation
```bash
pip install -r requirements.txt
```

## Usage
1. Clone the repo
2. Add `.env` file in sql-query-smolagent folder with the following environment variables:
   ```
   PG_DATABASE=your_database_name
   PG_USER=your_database_user
   PG_PASSWORD=your_database_password
   PG_HOST=your_database_host
   PG_PORT=your_database_port
   GEMINI_API_KEY=your_gemini_api_key
   ```
3. Run the Streamlit UI:
   ```python
   streamlit run bookstore-agent.py
   ```

## Dependencies
- smolagents
- streamlit
- sqlalchemy
- pandas
- python-dotenv