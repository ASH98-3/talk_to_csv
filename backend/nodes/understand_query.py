from backend.llm import call_llm
import json


def understand_query(state: dict) -> dict:
    question = state["question"]
    schema   = state["schema"]

    prompt = (
        "You are a data analysis expert. Analyse the user's question and return a JSON object.\n\n"
        f"Schema:\n{schema}\n\n"
        f"User question: {question}\n\n"
        "Return ONLY a JSON object with these exact keys:\n"
        "{\n"
        '  "path": "sql" or "pandas",\n'
        '  "rewritten_query": "cleaner version of the question for database querying",\n'
        '  "columns_needed": ["col1", "col2"],\n'
        '  "reasoning": "one line explanation of your decision",\n'
        '  "chart_type": "bar" or "line" or "pie" or "histogram" or "scatter" or null,\n'
        '  "chart_x": "column name for x axis" or null,\n'
        '  "chart_y": "column name for y axis" or null\n'
        "}\n\n"
        "Rules for path decision:\n"
        "- sql: aggregations, filters, groupby, counts, joins, top N, comparisons\n"
        "- pandas: correlation, distribution, missing values, shape, dtypes, describe, statistical analysis\n\n"
        "Rules for chart decision:\n"
        "- bar: comparisons across categories (salary by job title, count by country)\n"
        "- line: trends over time (postings by month)\n"
        "- pie: proportions (% remote vs non-remote, share by category)\n"
        "- histogram: distribution of a single numeric column\n"
        "- scatter: correlation between two numeric columns\n"
        "- null: if question is about a single value, missing values, shape, or not visual\n\n"
        "Return ONLY the JSON, no markdown, no explanation."
    )

    raw = call_llm(prompt).strip().strip("```").removeprefix("json").strip()

    try:
        parsed = json.loads(raw)
        return {
            **state,
            "path":            parsed.get("path", "sql"),
            "rewritten_query": parsed.get("rewritten_query", question),
            "columns_needed":  parsed.get("columns_needed", []),
            "reasoning":       parsed.get("reasoning", ""),
            "chart_type":      parsed.get("chart_type", None),
            "chart_x":         parsed.get("chart_x", None),
            "chart_y":         parsed.get("chart_y", None),
        }
    except json.JSONDecodeError:
        return {
            **state,
            "path":            "sql",
            "rewritten_query": question,
            "columns_needed":  [],
            "reasoning":       "fallback due to parse error",
            "chart_type":      None,
            "chart_x":         None,
            "chart_y":         None,
        }