from langgraph.graph import StateGraph, START, END
from state import PassedState
from nodes import get_table_schema, get_the_query, run_query, should_continue, give_final_answer, get_relevant_table

# 1. Initialize the graph with your State definition
builder = StateGraph(PassedState)

# 2. Define the Nodes
builder.add_node("get_table_schema", get_table_schema)
builder.add_node("get_the_query", get_the_query)
builder.add_node("run_query", run_query)
builder.add_node("give_final_answer", give_final_answer)
builder.add_node("get_relevant_table", get_relevant_table)

# 3. Define the Flow (Edges)
builder.add_edge(START, "get_table_schema")
builder.add_edge("get_table_schema", "get_relevant_table")
builder.add_edge("get_relevant_table", "get_the_query")
builder.add_edge("get_the_query", "run_query")
builder.add_edge("run_query", "give_final_answer")
builder.add_edge("give_final_answer", END)

# 4. Define the Logic Loop
# This matches the "re-try" logic to the run_query node
builder.add_conditional_edges(
    "run_query", 
    should_continue, 
    {
        "re-try": "get_the_query", # Loop back to generation to fix the query
        "done": "give_final_answer"
    }
)

graph = builder.compile()