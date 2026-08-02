from backend.llm import call_llm


def generate_sql(state: dict) -> dict:
    schema          = state["schema"]
    question        = state["question"]
    rewritten_query = state.get("rewritten_query", question)
    columns_needed  = state.get("columns_needed", [])
    error           = state.get("error", "")

    hint         = f"\nPrevious attempt failed: {error}\nFix the query." if error else ""
    columns_hint = f"\nFocus on these columns: {', '.join(columns_needed)}" if columns_needed else ""

    prompt = (
        "You are a SQLite expert. Write ONE SELECT query that answers the question.\n"
        "IMPORTANT: Use only standard SQLite functions.\n"
        "Do NOT use PERCENTILE_CONT, MEDIAN, PIVOT — not supported in SQLite.\n"
        "For distributions use AVG, MIN, MAX, COUNT instead.\n"
        "Return ONLY raw SQL — no markdown, no explanation.\n\n"
        f"{schema}\n\n"
        f"Question: {rewritten_query}"
        f"{columns_hint}"
        f"{hint}\n"
        "SQL:"
    )

    sql = call_llm(prompt).strip().strip("`").removeprefix("sql").strip()
    return {**state, "sql": sql, "error": ""}