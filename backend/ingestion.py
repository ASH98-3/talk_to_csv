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
    """
    Plain-text schema for LLM prompt.
    Fetches non-null samples per column independently so sparse columns
    like salary still get real sample values.
    Column names quoted to handle special characters and numbers.
    """
    conn = sqlite3.connect(db_path)
    cols = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    conn.close()

    col_lines = []
    for c in cols:
        col_name = c[1]
        col_type = c[2]
        try:
            conn    = sqlite3.connect(db_path)
            samples = conn.execute(
                f'SELECT "{col_name}" FROM {table_name} '
                f'WHERE "{col_name}" IS NOT NULL LIMIT 3'
            ).fetchall()
            conn.close()
            vals       = [str(row[0]) for row in samples]
            sample_str = ", ".join(vals) if vals else "no samples"
        except Exception:
            sample_str = "no samples"
        col_lines.append(f"  - {col_name} ({col_type}) e.g. {sample_str}")

    return f"Table: {table_name}\nColumns:\n" + "\n".join(col_lines)


def get_column_documents(db_path: str, table_name: str) -> list:
    """
    Build one text document per column for RAG embedding.
    Used by schema_store.py to populate ChromaDB.
    Column names quoted to handle special characters and numbers.
    """
    conn = sqlite3.connect(db_path)
    cols = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    conn.close()

    documents = []
    for c in cols:
        col_name = c[1]
        col_type = c[2]
        try:
            conn    = sqlite3.connect(db_path)
            samples = conn.execute(
                f'SELECT "{col_name}" FROM {table_name} '
                f'WHERE "{col_name}" IS NOT NULL LIMIT 3'
            ).fetchall()
            conn.close()
            vals       = [str(row[0]) for row in samples]
            sample_str = ", ".join(vals) if vals else "no samples"
        except Exception:
            sample_str = "no samples"
        documents.append(
            f"Table: {table_name} | Column: {col_name} | Type: {col_type} | Sample values: {sample_str}"
        )
    return documents


def get_dataframe(db_path: str, table_name: str) -> pd.DataFrame:
    """Load the full table as a DataFrame (used by pandas path)."""
    conn = sqlite3.connect(db_path)
    df   = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df