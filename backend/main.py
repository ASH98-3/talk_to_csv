import os
import uuid
import math
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.ingestion    import load_file, get_schema, get_column_documents, get_dataframe
from backend.schema_store import build_schema_store, get_relevant_schema
from backend.graph        import agent
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app      = FastAPI(title="TalkToCSV")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your Vercel URL after deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
DATA_DIR = Path("backend/data")
DATA_DIR.mkdir(exist_ok=True)

sessions: dict = {}


class AskRequest(BaseModel):
    session_id: str
    question:   str


def safe_json(obj):
    """Recursively replace NaN/Inf with None so response serializes cleanly."""
    if isinstance(obj, list):
        return [safe_json(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: safe_json(v) for k, v in obj.items()}
    elif isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    return obj


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in {".csv", ".xlsx", ".xls"}:
        raise HTTPException(400, "Only CSV and Excel files are supported.")

    session_id = str(uuid.uuid4())
    file_path  = DATA_DIR / f"{session_id}{ext}"
    db_path    = str(DATA_DIR / f"{session_id}.db")

    file_path.write_bytes(await file.read())

    table_name = load_file(str(file_path), db_path)
    schema     = get_schema(db_path, table_name)
    df         = get_dataframe(db_path, table_name)
    documents  = get_column_documents(db_path, table_name)

    build_schema_store(documents, session_id)

    sessions[session_id] = {
        "db_path":    db_path,
        "table_name": table_name,
        "schema":     schema,
        "df":         df,
        "col_count":  len(df.columns),
    }

    return JSONResponse(content=safe_json({
        "session_id": session_id,
        "table":      table_name,
        "rows":       len(df),
        "columns":    list(df.columns),
        "preview":    df.head(5).to_dict(orient="records"),
    }))


@app.post("/ask")
def ask(req: AskRequest):
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(404, "Session not found. Please upload a file first.")

    col_count = session["col_count"]

    if col_count > 40:
        generation_schema = get_relevant_schema(
            question=req.question,
            session_id=req.session_id,
            table_name=session["table_name"],
            n_results=min(col_count, 10),
        )
    else:
        generation_schema = session["schema"]

    result = agent.invoke({
        "question":        req.question,
        "schema":          generation_schema,
        "db_path":         session["db_path"],
        "df":              session["df"],
        "path":            "",
        "rewritten_query": "",
        "columns_needed":  [],
        "reasoning":       "",
        "chart_type":      None,
        "chart_x":         None,
        "chart_y":         None,
        "sql":             None,
        "pandas_code":     None,
        "result":          None,
        "error":           "",
        "retries":         0,
        "answer":          None,
        "table":           None,
    })

    return JSONResponse(content=safe_json({
        "answer":      result["answer"],
        "sql":         result.get("sql"),
        "pandas_code": result.get("pandas_code"),
        "table":       result.get("table"),
        "reasoning":   result.get("reasoning"),
        "chart_type":  result.get("chart_type"),
        "chart_x":     result.get("chart_x"),
        "chart_y":     result.get("chart_y"),
    }))