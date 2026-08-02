from backend.llm import call_llm


def generate_pandas(state: dict) -> dict:
    schema          = state["schema"]
    question        = state["question"]
    rewritten_query = state.get("rewritten_query", question)
    columns_needed  = state.get("columns_needed", [])

    columns_hint = f"\nFocus on these columns: {', '.join(columns_needed)}" if columns_needed else ""

    prompt = (
        "You are a pandas expert. Write ONE pandas expression that answers the question.\n"
        "The DataFrame is already loaded as `df`.\n"
        "Return ONLY the expression — no imports, no assignment, no markdown.\n\n"
        f"{schema}\n\n"
        f"Question: {rewritten_query}"
        f"{columns_hint}\n"
        "Expression:"
    )

    code = call_llm(prompt).strip().strip("`").removeprefix("python").strip()
    return {**state, "pandas_code": code, "error": ""}