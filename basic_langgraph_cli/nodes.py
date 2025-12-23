import os
import psycopg2
import requests
from state import PassedState

# Helper to get DB connection using env variables or defaults
def get_db_connection():
    return psycopg2.connect(
        database=os.getenv("POSTGRES_DB", "postgres"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", 5432)
    )

def get_table_schema(state: PassedState):
    schema = {}
    conn = get_db_connection()
    curr = conn.cursor()

    curr.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name='students'
    """)

    data = curr.fetchall()
    for column, dtype in data:
        schema[column] = dtype
    
    curr.close()
    conn.close()
    return {"schema": schema}

def get_the_query(state: PassedState):
    error_context = f"\nPrevious error: {state.get('error')}" if state.get('error') else ""
    
    prompt = (
        f"You are a Postgres SQL agent. Table: 'students'. "
        f"Schema: {state['schema']}. "
        f"Question: {state['question']}{error_context} "
        f"Respond ONLY with the SQL query."
    )

    data = {
        "model": "llama3.2",
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post("http://localhost:11434/api/generate", json=data)
        query = response.json().get("response").strip()
        return {"query": query}
    except Exception as e:
        return {"error": f"LLM Connection Error: {str(e)}"}

def run_query(state: PassedState):
    conn = get_db_connection()
    curr = conn.cursor()
    attempts = state.get('attempts', 0)
    
    try:
        curr.execute(state['query'])
        result = curr.fetchall()
        curr.close()
        conn.close()
        return {"result": result, "error": None, "attempts": attempts + 1}
    except Exception as e:
        if curr: curr.close()
        if conn: conn.close()
        return {"result": None, "error": str(e), "attempts": attempts + 1}

def should_continue(state: PassedState) -> str:
    # If there's an error and we have tries left, go back to 'get_the_query'
    if state.get('error') and state.get('attempts', 0) < 3:
        return "re-try"
    return "done"

def give_final_answer(state: PassedState):
    if state['error']:
        final_answer = f"failed to executte the query. last error: {state['error']}"
    else:
        prompt = f"you will be given output of text to sql query executed from table students. here is the schema {state['schema']}. and here is the result of the sql query {state['result']}. and here is the query that was executed {state['query']}. rephrase the answer in natural language for the user to understand."
        data = {
            "model": "llama3.2",
            "prompt": prompt,
            "stream": False
        }
        response = requests.post("http://localhost:11434/api/generate", json = data)
        final_answer = response.json().get("response").strip()
    return {"final_answer": final_answer}

