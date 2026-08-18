import os
from typing import Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from nexus import BloxyNexus

app = FastAPI(title="Bloxy Nexus", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"https://[A-Za-z0-9-]+\.base44\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

nexus = BloxyNexus()

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20000)
    conversation_id: str | None = None
    stream: bool = False

@app.get("/")
async def root():
    return {"name": "Bloxy Nexus", "service": "Bloxy-bot AI engine", "sources": nexus.source_count}

@app.get("/health")
async def health():
    return {"status": "ok", "service": "bloxy-nexus", "sources": nexus.source_count}

@app.get("/ready")
async def ready():
    return {"ready": True, "ai_providers": nexus.ai_provider_count, "sources": nexus.source_count}

@app.get("/ai/providers")
async def providers():
    return nexus.provider_summary()

@app.get("/ai/providers/health")
async def provider_health():
    return await nexus.health()

@app.post("/ai/chat")
async def chat(request: ChatRequest):
    try:
        result = await nexus.answer(request.message, request.conversation_id)
        if request.stream:
            async def body():
                yield result["answer"]
            return StreamingResponse(body(), media_type="text/plain; charset=utf-8")
        return result
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Bloxy Nexus could not complete the request: {type(exc).__name__}") from exc

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
