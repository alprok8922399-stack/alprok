from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

class ChatRequest(BaseModel):
    session_id: str
    message: str

@app.post("/chat")
async def chat(req: ChatRequest):
    if not openai.api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":req.message}],
            temperature=0.7,
            max_tokens=500,
        )
        return {"reply": resp.choices[0].message["content"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
