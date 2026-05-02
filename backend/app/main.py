from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os, httpx

app = FastAPI()

class ChatRequest(BaseModel):
    session_id: str
    message: str

HISTORY = {}
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

@app.post("/chat")
async def chat(req: ChatRequest):
    if not OPENAI_KEY:
        raise HTTPException(status_code=500, detail="No model API key configured")
    HISTORY.setdefault(req.session_id, []).append({"role":"user","content":req.message})
    payload = {"model": "gpt-4o-mini", "messages": HISTORY[req.session_id]}
    headers = {"Authorization": f"Bearer {OPENAI_KEY}"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail="Model API error")
    data = r.json()
    reply = data["choices"][0]["message"]["content"]
    HISTORY[req.session_id].append({"role":"assistant","content":reply})
    return {"reply": reply}
  
