from contextlib import asynccontextmanager
from fastapi import Depends
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from config import settings
from database import Base
from database import engine
from exceptions import AuthenticationError
from exceptions import ValidationError
import httpx

from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import AIProvider


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    from database import SessionLocal

    db = SessionLocal()

    try:
        for provider in DEFAULT_PROVIDERS:
            existing = (
                db.query(AIProvider)
                .filter(AIProvider.name == provider["name"])
                .first()
            )

            if not existing:
                db.add(
                    AIProvider(
                        name=provider["name"],
                        base_url=provider["base_url"],
                        description=provider["description"],
                    )
                )

        db.commit()

    finally:
        db.close()

    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)


@app.exception_handler(ValidationError)
async def validation_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": exc.message,
        },
    )


@app.exception_handler(AuthenticationError)
async def authentication_error_handler(request, exc):
    return JSONResponse(
        status_code=401,
        content={
            "success": False,
            "error": exc.message,
        },
    )


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
    }
    @app.get("/ai/providers/health")
async def provider_health():
    results = {}

    async with httpx.AsyncClient(timeout=10.0) as client:

        for provider in DEFAULT_PROVIDERS:

            try:
                response = await client.get(
                    provider["base_url"]
                )

                results[provider["name"]] = {
                    "online": response.status_code < 500,
                    "status_code": response.status_code,
                }

            except Exception:
                results[provider["name"]] = {
                    "online": False,
                    "status_code": None,
                }

    return results


@app.get("/ready")
async def readiness():
    return {
        "ready": True,
    }
    class ChatRequest(BaseModel):
    provider: str
    prompt: str


class ProviderResponse(BaseModel):
    name: str
    enabled: bool
    base_url: str
    DEFAULT_PROVIDERS = [
    {
        "name": "openai",
        "base_url": "https://api.openai.com/v1",
        "description": "OpenAI API",
    },
    {
        "name": "openrouter",
        "base_url": "https://openrouter.ai/api/v1",
        "description": "OpenRouter API",
    },
    {
        "name": "groq",
        "base_url": "https://api.groq.com/openai/v1",
        "description": "Groq API",
    },
    {
        "name": "kimi",
        "base_url": "https://api.moonshot.ai/v1",
        "description": "Kimi API",
    },
]
    @app.get("/ai/providers")
def list_providers(db: Session = Depends(get_db)):
    providers = db.query(AIProvider).all()

    return [
        {
            "name": p.name,
            "enabled": p.enabled,
            "base_url": p.base_url,
        }
        for p in providers
    ]
    @app.post("/ai/chat")
async def ai_chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    provider = (
        db.query(AIProvider)
        .filter(AIProvider.name == request.provider)
        .first()
    )

    if not provider:
        raise ValidationError(
            f"Unknown provider: {request.provider}"
        )

    if not provider.enabled:
        raise ValidationError(
            f"Provider disabled: {request.provider}"
        )

    return {
        "provider": provider.name,
        "status": "accepted",
        "message": "Provider routing established",
        "prompt_length": len(request.prompt),
    }
    
    
    
    
   
