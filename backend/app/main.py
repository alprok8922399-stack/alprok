from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import openai
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI(title="Minimal AI Chat")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


if not OPENAI_API_KEY:
    # raise at import time so CI/local run fails fast when secret missing
    raise RuntimeError("OPENAI_API_KEY is not set")


openai.api_key = OPENAI_API_KEY


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # замените на нужную модель или моки для CI
            messages=[{"role": "user", "content": req.message}],
            max_tokens=150,
        )
        text = resp.choices[0].message.content.strip()
        return ChatResponse(reply=text)
    except Exception as exc:
        # логируем исключение и возвращаем 502
        raise HTTPException(status_code=502, detail="AI backend error")
