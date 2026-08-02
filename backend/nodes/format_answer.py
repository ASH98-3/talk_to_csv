import pandas as pd
from backend.llm import call_llm


def format_answer(state: dict) -> dict:
    result   = state["result"]
    question = state["question"]
    sql      = state.get("sql", "")
    pandas_code = state.get("pandas_code", "")

    if result is None:
        return {**state, "answer": "Sorry, I could not answer that question.", "table": None}

    if isinstance(result, pd.DataFrame):
        result_str = result.to_string(index=False)
        table      = result.to_dict(orient="records")
    else:
        result_str = str(result)
        table      = None

    prompt = (
        "Answer the question using ONLY the data in the result below.\n"
        "Do NOT add any outside knowledge, estimates, or general statistics.\n"
        "Be specific — use only actual numbers from the result.\n"
        "Keep it to 1-2 sentences.\n\n"
        f"Question: {question}\nResult:\n{result_str}\n\nAnswer:"
    )

    summary = call_llm(prompt)

    return {
        **state,
        "answer":      summary,
        "table":       table,
        "sql":         sql,
        "pandas_code": pandas_code,
    }