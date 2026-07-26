from groq import Groq

client = Groq()  # reads GROQ_API_KEY from env
MODEL = "llama-3.3-70b-versatile"  # fast, free tier, great at SQL
MAX_TOKENS = 512


def call_llm(prompt: str) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content.strip()
