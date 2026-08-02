from backend.sql_safety import execute


def execute_sql(state: dict) -> dict:
    try:
        df = execute(state["sql"], state["db_path"])
        return {**state, "result": df, "error": ""}
    except Exception as e:
        return {**state, "result": None, "error": str(e)}