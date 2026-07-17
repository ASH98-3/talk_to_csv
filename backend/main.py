import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel

from backend.ingestion import load_file, get_schema, get_dataframe
from backend.graph import agent

load_dotenv()

app = FastAPI(title="Dataset Analyzer")

DATA_DIR = Path("backend/data")
DATA_DIR.mkdir(exist_ok=True)

# In-memory session store: session_id -> {db_path, table_name, schema, df}
sessions: dict = {}


# --- Schemas ---

class AskRequest(BaseModel):
    session_id: str
    question: str


class AskResponse(BaseModel):
    answer: str
    sql: str | None
    pandas_code: str | None
    table: list | None


# --- Endpoints ---

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in {".csv", ".xlsx", ".xls"}:
        raise HTTPException(400, "Only CSV and Excel files are supported.")

    session_id = str(uuid.uuid4())
    file_path = DATA_DIR / f"{session_id}{ext}"
    db_path = str(DATA_DIR / f"{session_id}.db")

    # save upload to disk
    file_path.write_bytes(await file.read())

    table_name = load_file(str(file_path), db_path)
    schema = get_schema(db_path, table_name)
    df = get_dataframe(db_path, table_name)

    sessions[session_id] = {
        "db_path": db_path,
        "table_name": table_name,
        "schema": schema,
        "df": df,
    }

    return {
        "session_id": session_id,
        "table": table_name,
        "rows": len(df),
        "columns": list(df.columns),
        "preview": df.head(5).to_dict(orient="records"),
    }


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(404, "Session not found. Please upload a file first.")

    result = agent.invoke({
        "question": req.question,
        "schema": session["schema"],
        "db_path": session["db_path"],
        "df": session["df"],
        "sql": None,
        "pandas_code": None,
        "result": None,
        "error": "",
        "retries": 0,
        "answer": None,
        "table": None,
    })

    return AskResponse(
        answer=result["answer"],
        sql=result.get("sql"),
        pandas_code=result.get("pandas_code"),
        table=result.get("table"),
    )