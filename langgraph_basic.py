from typing import TypedDict 
import psycopg2
from langgraph.graph import StateGraph, START, END
import requests
from langchain_core.tools import tool
from pydantic import BaseModel, field_validator
import re

schema = {}
user_question = input("enter yo question: ")

class passed_state(TypedDict):
    question: str
    schema: dict
    query: str
    result: str

def get_table_schema(state: passed_state):
    conn = psycopg2.connect(database="postgres",
                                user="postgres",
                                password="postgres",
                                port=5432)

    curr = conn.cursor()

    curr.execute("""SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name='students'""")

    data = curr.fetchall()
    
    for column, type in data:
        schema[column] = type

    return {'schema': schema}

def get_the_query(state: passed_state):
    data ={
        "model": "llama3.2",
        "prompt" : f"you are a postgres sql agent that converts natural language to postgres sql queries. given the table schema {state['schema']} write sql query for the question {state['question']} dont give anything other than the query. name of the table is 'students'",
        "stream": False
    }

    response = requests.post("http://localhost:11434/api/generate", json = data)

    return {'query' : response.json().get("response")}

def run_query(state: passed_state):
    conn = psycopg2.connect(database="postgres",
                                user="postgres",
                                password="postgres",
                                port=5432)

    curr = conn.cursor()

    curr.execute(state['query'])

    return {'result' : curr.fetchall()}


graph = StateGraph(passed_state)

graph.add_node('get_table_schema', get_table_schema)
graph.add_node('get_the_query', get_the_query)
graph.add_node('run_query', run_query)

graph.add_edge(START, 'get_table_schema')
graph.add_edge('get_table_schema', 'get_the_query')
graph.add_edge('get_the_query', 'run_query')
graph.add_edge('run_query' , END)

workflow = graph.compile()

initial_state = {
    "question" : user_question,
    "schema" : "",
    "query" : "",
    "result" : ""
}

final_state = workflow.invoke(initial_state)

print(final_state['result'])
