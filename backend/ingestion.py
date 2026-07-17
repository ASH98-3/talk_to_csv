import sqlite3
import pandas as pd


def load_file(file_path: str, db_path: str, table_name: str = "data") -> str:
    """Load a CSV or Excel file into SQLite. Returns the table name."""
    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)

    # clean column names: lowercase, spaces -> underscores
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    conn = sqlite3.connect(db_path)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()
    return table_name


def get_schema(db_path: str, table_name: str) -> str:
    """Return a plain-text schema description for the LLM prompt."""
    conn = sqlite3.connect(db_path)
    cols = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    sample = conn.execute(f"SELECT * FROM {table_name} LIMIT 3").fetchall()
    conn.close()

    col_lines = [f"  - {c[1]} ({c[2]})" for c in cols]
    sample_lines = [str(row) for row in sample]

    return (
        f"Table: {table_name}\n"
        f"Columns:\n" + "\n".join(col_lines) + "\n"
        f"Sample rows:\n" + "\n".join(sample_lines)
    )


def get_dataframe(db_path: str, table_name: str) -> pd.DataFrame:
    """Load the full table as a DataFrame (used by pandas path)."""
    conn = sqlite3.connect(db_path)
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df