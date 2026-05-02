from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import openai
import asyncio
from typing import Optional

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set in environment")

openai.api_key = OPENAI_API_KEY

app = FastAPI(title="Minimal Chat AI")

class ChatRequest(BaseModel):
    message: str
    system: Optional[str] = "You are a helpful assistant."
    model: Optional[str] = "gpt-4o-mini"  # change if needed
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7

class ChatResponse(BaseModel):
    reply: str

async def call_openai_completion(request: ChatRequest) -> str:
    try:
        resp = await asyncio.to_thread(
            lambda: openai.ChatCompletion.create(
                model=request.model,
                messages=[
                    {"role": "system", "content": request.system},
                    {"role": "user", "content": request.message},
                ],
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            )
        )
        # safe access
        choices = resp.get("choices") or []
        if not choices:
            return "No response from model."
        return choices[0].get("message", {}).get("content", "").strip()
    except Exception as e:
        raise

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    try:
        reply = await call_openai_completion(req)
        return ChatResponse(reply=reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
