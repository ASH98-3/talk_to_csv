from backend.llm import call_llm


def generate_sql(state: dict) -> dict:
    schema          = state["schema"]
    question        = state["question"]
    rewritten_query = state.get("rewritten_query", question)
    columns_needed  = state.get("columns_needed", [])
    error           = state.get("error", "")
    chart_type      = state.get("chart_type")

    hint         = f"\nPrevious attempt failed: {error}\nFix the query." if error else ""
    columns_hint = f"\nFocus on these columns: {', '.join(columns_needed)}" if columns_needed else ""
    
    chart_hint = ""
    if chart_type in ["bar", "pie", "line"]:
        chart_hint = (
            f"\nIMPORTANT: Since this needs a {chart_type} chart, "
            f"structure the result with one row per category. "
            f"Use two columns: one for the category ({state.get('chart_x', 'category')}) "
            f"and one for the value ({state.get('chart_y', 'value')}). "
            f"Do NOT use multiple value columns side by side."
        )

    prompt = (
        "You are a SQLite expert. Write ONE SELECT query that answers the question.\n"
        "IMPORTANT: Use only standard SQLite functions.\n"
        "Do NOT use PERCENTILE_CONT, MEDIAN, PIVOT — not supported in SQLite.\n"
        "For distributions use AVG, MIN, MAX, COUNT instead.\n"
        "Return ONLY raw SQL — no markdown, no explanation.\n\n"
        f"{schema}\n\n"
        f"Question: {rewritten_query}"
        f"{columns_hint}"
        f"{chart_hint}"
        f"{hint}\n"
        "SQL:"
    )

    sql = call_llm(prompt).strip().strip("`").removeprefix("sql").strip()
    return {**state, "sql": sql, "error": ""}