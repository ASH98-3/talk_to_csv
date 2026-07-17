import sqlite3
import pandas as pd

ROW_CAP = 100  # never return more than this to the LLM


def is_safe(sql: str) -> bool:
    """Only allow SELECT statements."""
    return sql.strip().lower().startswith("select")


def execute(sql: str, db_path: str) -> pd.DataFrame:
    """Run a safe SQL query, capped at ROW_CAP rows."""
    if not is_safe(sql):
        raise ValueError(f"Only SELECT queries are allowed. Got: {sql[:80]}")

    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df.head(ROW_CAP)