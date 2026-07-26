PANDAS_KEYWORDS = [
    "correlation", "distribution", "describe", "summary", "statistics",
    "std", "mean", "median", "variance", "plot", "trend", "missing",
    "null", "shape", "how many rows", "how many columns", "columns",
    "data types", "dtypes", "head", "tail", "info",
]


def route(question: str) -> str:
    """
    Returns 'pandas' or 'sql'.
    Simple keyword check — fast, zero tokens used.
    """
    q = question.lower()
    if any(kw in q for kw in PANDAS_KEYWORDS):
        return "pandas"
    return "sql"