from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
import pandas as pd

from backend.nodes.understand_query import understand_query
from backend.nodes.generate_sql     import generate_sql
from backend.nodes.execute_sql      import execute_sql
from backend.nodes.generate_pandas  import generate_pandas
from backend.nodes.execute_pandas   import execute_pandas
from backend.nodes.format_answer    import format_answer


class AgentState(TypedDict):
    question:        str
    schema:          str
    db_path:         str
    df:              Optional[pd.DataFrame]
    # query understanding
    path:            str
    rewritten_query: str
    columns_needed:  list
    reasoning:       str
    chart_type:      Optional[str]
    chart_x:         Optional[str]
    chart_y:         Optional[str]
    # execution
    sql:             Optional[str]
    pandas_code:     Optional[str]
    result:          Optional[object]
    error:           str
    retries:         int
    # output
    answer:          Optional[str]
    table:           Optional[list]


def pick_path(state: AgentState) -> str:
    return state.get("path", "sql")


def should_retry(state: AgentState) -> str:
    if state["error"] and state["retries"] < 2:
        return "retry"
    return "format"


def build_graph():
    g = StateGraph(AgentState)

    g.add_node("understand_query", understand_query)
    g.add_node("generate_sql",     generate_sql)
    g.add_node("execute_sql",      execute_sql)
    g.add_node("generate_pandas",  generate_pandas)
    g.add_node("execute_pandas",   execute_pandas)
    g.add_node("format_answer",    format_answer)

    g.set_entry_point("understand_query")

    g.add_conditional_edges("understand_query", pick_path, {
        "sql":    "generate_sql",
        "pandas": "generate_pandas",
    })

    g.add_edge("generate_sql", "execute_sql")
    g.add_conditional_edges("execute_sql", should_retry, {
        "retry":  "generate_sql",
        "format": "format_answer",
    })

    g.add_edge("generate_pandas", "execute_pandas")
    g.add_edge("execute_pandas",  "format_answer")
    g.add_edge("format_answer",   END)

    return g.compile()


agent = build_graph()