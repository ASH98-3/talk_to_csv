from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
import pandas as pd

from backend.nodes.generate_sql import generate_sql
from backend.nodes.execute_sql import execute_sql
from backend.nodes.generate_pandas import generate_pandas
from backend.nodes.execute_pandas import execute_pandas
from backend.nodes.format_answer import format_answer
from backend.pandas_router import route


# --- State ---

class AgentState(TypedDict):
    question: str
    schema: str
    db_path: str
    df: Optional[pd.DataFrame]   # for pandas path
    sql: Optional[str]
    pandas_code: Optional[str]
    result: Optional[object]
    error: str
    retries: int
    answer: Optional[str]
    table: Optional[list]


# --- Routing functions ---

def router_node(state: AgentState) -> AgentState:
    """Decide which path to take — stored in state so the graph can branch."""
    path = route(state["question"])
    return {**state, "path": path}


def pick_path(state: AgentState) -> str:
    return state.get("path", "sql")


def should_retry(state: AgentState) -> str:
    """After SQL execute: retry if error and under retry limit, else format."""
    if state["error"] and state["retries"] < 2:
        return "retry"
    return "format"


# --- Build graph ---

def build_graph():
    g = StateGraph(AgentState)

    g.add_node("router", router_node)
    g.add_node("generate_sql", generate_sql)
    g.add_node("execute_sql", execute_sql)
    g.add_node("generate_pandas", generate_pandas)
    g.add_node("execute_pandas", execute_pandas)
    g.add_node("format_answer", format_answer)

    g.set_entry_point("router")

    g.add_conditional_edges("router", pick_path, {
        "sql": "generate_sql",
        "pandas": "generate_pandas",
    })

    # SQL path: generate → execute → retry or format
    g.add_edge("generate_sql", "execute_sql")
    g.add_conditional_edges("execute_sql", should_retry, {
        "retry": "generate_sql",
        "format": "format_answer",
    })

    # Pandas path: generate → execute → format (no retry for now)
    g.add_edge("generate_pandas", "execute_pandas")
    g.add_edge("execute_pandas", "format_answer")

    g.add_edge("format_answer", END)

    return g.compile()


agent = build_graph()