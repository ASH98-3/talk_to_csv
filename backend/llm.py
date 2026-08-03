from groq import Groq
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment or .env file")

client     = Groq(api_key=GROQ_API_KEY)
MODEL      = "llama-3.3-70b-versatile"
MAX_TOKENS = 500


def call_llm(prompt: str) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content.strip()