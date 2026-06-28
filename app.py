# =============================================================
#  BLOXY-BOT AI — app.py
#  Complete Production FastAPI Backend
#  Python 3.11 · Render-compatible · 3000+ lines
# =============================================================

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import io
import json
import logging
import math
import os
import re
import secrets
import time
import traceback
import urllib.parse
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import httpx
import jwt
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker

# =============================================================
# LOGGING
# =============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("bloxy-bot")

# =============================================================
# CONFIGURATION
# =============================================================

ADMIN_EMAILS = {
    "alvinogthegreat177@gmail.com",
    "alvinogthegreat177@outlook.com",
}


class Config:
    SECRET_KEY           = os.getenv("SECRET_KEY", secrets.token_hex(32))
    DATABASE_URL         = os.getenv("DATABASE_URL", "sqlite:///./bloxy_bot.db")
    ENVIRONMENT          = os.getenv("ENVIRONMENT", "production")
    BASE_URL             = os.getenv("BASE_URL", "http://localhost:8000")
    JWT_ALGORITHM        = "HS256"
    JWT_EXPIRE_DAYS      = 30
    SESSION_COOKIE       = "bloxy_session"

    # AI Providers
    OPENAI_API_KEY       = os.getenv("OPENAI_API_KEY", "")
    OPENROUTER_API_KEY   = os.getenv("OPENROUTER_API_KEY", "")
    GROQ_API_KEY         = os.getenv("GROQ_API_KEY", "")
    KIMI_API_KEY         = os.getenv("KIMI_API_KEY", "")
    DEEPSEEK_API_KEY     = os.getenv("DEEPSEEK_API_KEY", "")
    MISTRAL_API_KEY      = os.getenv("MISTRAL_API_KEY", "")
    COHERE_API_KEY       = os.getenv("COHERE_API_KEY", "")
    HUGGINGFACE_API_KEY  = os.getenv("HUGGINGFACE_API_KEY", "")
    CLAUDE_API_KEY       = os.getenv("CLAUDE_API_KEY", "")

    # Search
    TAVILY_API_KEY       = os.getenv("TAVILY_API_KEY", "")
    EXA_API_KEY          = os.getenv("EXA_API_KEY", "")
    FIRECRAWL_API_KEY    = os.getenv("FIRECRAWL_API_KEY", "")
    SEARCH_API_KEY       = os.getenv("SEARCH_API_KEY", os.getenv("SEARCH_API-KEY", ""))

    # News
    NEWS_API_KEY         = os.getenv("NEWS_API_KEY", "")
    GNEWS_API_KEY        = os.getenv("GNEWS_API_KEY", "")
    GUARDIAN_API_KEY     = os.getenv("GUARDIAN_API_KEY", "")
    MEDIASTACK_API_KEY   = os.getenv("MEDIASTACK_API_KEY", "")

    # Weather
    OPENWEATHER_API_KEY  = os.getenv("OPENWEATHER_API_KEY", "")
    TOMORROW_IO_KEY      = os.getenv("TOMORROW.IO_API_KEY", "")

    # Finance
    ALPHA_VANTAGE_KEY    = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    FINNHUB_API_KEY      = os.getenv("FINNHUB_API_KEY", "")
    EXCHANGERATE_KEY     = os.getenv("EXCHANGERATE_API_KEY", "")
    EXCHANGERATE_HOST    = os.getenv("EXCHANGERATE.HOST_API_KEY", "")
    COINGECKO_API_KEY    = os.getenv("COINGECKO_API_KEY", "")
    TWELVEDATA_KEY       = os.getenv("TWELVEDATA_API_KEY", "")

    # Sports
    SPORTRADAR_KEY       = os.getenv("SPORTRADAR_API_KEY", "")
    SPORTMONK_KEY        = os.getenv("SPORTMONK_API_KEY", "")
    APISPORTS_KEY        = os.getenv("APISPORTS_API_KEY", "")
    THESPORTSDB_KEY      = os.getenv("THESPORTSDB_API_KEY", "123")
    ALLSPORTS_KEY        = os.getenv("ALLSPORTS_API_KEY", "")
    ODDS_API_KEY         = os.getenv("ODDS_API_KEY", "")

    # Entertainment
    TMDB_API_KEY         = os.getenv("TMDB_API_KEY", "")
    OMDB_API_KEY         = os.getenv("OMDB_API_KEY", "")

    # Geo & Location
    GEOAPIFY_KEY         = os.getenv("GEOAPIFY_API_KEY", "")
    IPINFO_KEY           = os.getenv("IPINFO.IO_API_KEY", "")
    TIMEZONEDB_KEY       = os.getenv("TIMEZONEDB_API_KEY", "")

    # Misc
    RESEND_API_KEY       = os.getenv("RESEND_API_KEY", "")
    WOLFRAM_APP_ID       = os.getenv("WOLFRAM_APP_ID", "")

    # OAuth
    GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GITHUB_CLIENT_ID     = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")


# =============================================================
# DATABASE
# =============================================================

db_url = Config.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
engine = create_engine(db_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id          = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name        = Column(String, nullable=False)
    email       = Column(String, unique=True, nullable=False, index=True)
    password    = Column(String, nullable=True)
    provider    = Column(String, default="email")
    provider_id = Column(String, nullable=True)
    role        = Column(String, default="user")
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    chats       = relationship("Chat", back_populates="user", cascade="all, delete-orphan")


class Chat(Base):
    __tablename__ = "chats"
    id            = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id       = Column(String, ForeignKey("users.id"), nullable=True)
    title         = Column(String, default="New Chat")
    model         = Column(String, default="gpt-4o")
    provider      = Column(String, default="openai")
    message_count = Column(Integer, default=0)
    total_tokens  = Column(Integer, default=0)
    created_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user          = relationship("User", back_populates="chats")
    messages      = relationship("Message", back_populates="chat", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"
    id         = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    chat_id    = Column(String, ForeignKey("chats.id"), nullable=False)
    role       = Column(String, nullable=False)
    content    = Column(Text, nullable=False)
    model      = Column(String, nullable=True)
    tokens     = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    chat       = relationship("Chat", back_populates="messages")


class ApiUsageLog(Base):
    __tablename__ = "api_usage_logs"
    id         = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider   = Column(String, nullable=False)
    model      = Column(String, nullable=True)
    tokens     = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    status     = Column(String, default="success")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SystemLog(Base):
    __tablename__ = "system_logs"
    id         = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    level      = Column(String, default="INFO")
    message    = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ErrorLog(Base):
    __tablename__ = "error_logs"
    id         = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    message    = Column(Text, nullable=False)
    traceback  = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id         = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id    = Column(String, ForeignKey("users.id"), nullable=False)
    token      = Column(String, unique=True, nullable=False, index=True)
    used       = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    _log_system_internal("INFO", "Database initialized successfully.")


def _log_system_internal(level: str, message: str):
    try:
        db = SessionLocal()
        db.add(SystemLog(level=level, message=message[:2000]))
        db.commit()
        db.close()
    except Exception:
        pass
    getattr(logger, level.lower(), logger.info)(message)


def _log_error_internal(message: str, tb: str = ""):
    try:
        db = SessionLocal()
        db.add(ErrorLog(message=message[:2000], traceback=tb[:5000]))
        db.commit()
        db.close()
    except Exception:
        pass
    logger.error(message)


def _log_api_usage_internal(provider: str, model: str, tokens: int, latency_ms: int, status: str = "success"):
    try:
        db = SessionLocal()
        db.add(ApiUsageLog(provider=provider, model=model, tokens=tokens, latency_ms=latency_ms, status=status))
        db.commit()
        db.close()
    except Exception:
        pass


# =============================================================
# SCHEMAS
# =============================================================

class RegisterRequest(BaseModel):
    name:     str = Field(..., min_length=1, max_length=100)
    email:    str
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    email:    str
    password: str
    remember: bool = True


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token:    str
    password: str = Field(..., min_length=8)


class ChatRequest(BaseModel):
    messages:      List[Dict[str, Any]]
    model:         str = "gpt-4o"
    provider:      str = "openai"
    tool:          Optional[str] = None
    web_search:    bool = False
    max_tokens:    int = Field(default=4096, ge=1, le=32000)
    temperature:   float = Field(default=0.7, ge=0.0, le=2.0)
    system_prompt: Optional[str] = None
    stream:        bool = True
    chat_id:       Optional[str] = None


class ToolRequest(BaseModel):
    tool:    str
    input:   str
    options: Optional[Dict[str, Any]] = {}


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None


# =============================================================
# UTILITIES
# =============================================================

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260000)
    return f"{salt}:{h.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    try:
        salt, h = hashed.split(":", 1)
        check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260000)
        return hmac.compare_digest(check.hex(), h)
    except Exception:
        return False


def create_jwt(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=Config.JWT_EXPIRE_DAYS),
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm=Config.JWT_ALGORITHM)


def decode_jwt(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])
    except Exception:
        return None


def user_to_dict(user: User) -> dict:
    return {
        "id":         user.id,
        "name":       user.name,
        "email":      user.email,
        "role":       "admin" if user.email in ADMIN_EMAILS else user.role,
        "provider":   user.provider,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def set_auth_cookie(response: Response, token: str, remember: bool = True):
    response.set_cookie(
        key=Config.SESSION_COOKIE,
        value=token,
        httponly=True,
        secure=Config.ENVIRONMENT == "production",
        samesite="lax",
        max_age=60 * 60 * 24 * 30 if remember else None,
    )


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    token = request.cookies.get(Config.SESSION_COOKIE)
    if not token:
        return None
    payload = decode_jwt(token)
    if not payload:
        return None
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    return user if user and user.is_active else None


def require_user(user: Optional[User] = Depends(get_current_user)) -> User:
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return user


def require_admin(user: Optional[User] = Depends(get_current_user)) -> User:
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    if user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required.")
    return user


def sanitize_text(text: str, max_length: int = 10000) -> str:
    if not text:
        return ""
    return str(text)[:max_length].strip()


def count_tokens_approx(text: str) -> int:
    return max(1, len(text) // 4)


# =============================================================
# AI PROVIDER CONFIGS
# =============================================================

PROVIDER_CONFIGS: Dict[str, dict] = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "key":      lambda: Config.OPENAI_API_KEY,
        "type":     "openai_compat",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "key":      lambda: Config.OPENROUTER_API_KEY,
        "type":     "openai_compat",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "key":      lambda: Config.GROQ_API_KEY,
        "type":     "openai_compat",
    },
    "kimi": {
        "base_url": "https://api.moonshot.cn/v1",
        "key":      lambda: Config.KIMI_API_KEY,
        "type":     "openai_compat",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "key":      lambda: Config.DEEPSEEK_API_KEY,
        "type":     "openai_compat",
    },
    "mistral": {
        "base_url": "https://api.mistral.ai/v1",
        "key":      lambda: Config.MISTRAL_API_KEY,
        "type":     "openai_compat",
    },
    "cohere": {
        "base_url": "https://api.cohere.ai/v1",
        "key":      lambda: Config.COHERE_API_KEY,
        "type":     "cohere",
    },
    "claude": {
        "base_url": "https://api.anthropic.com/v1",
        "key":      lambda: Config.CLAUDE_API_KEY,
        "type":     "claude",
    },
}

TOOL_SYSTEM_PROMPTS: Dict[str, str] = {
    "web_search":     "You are a research assistant with access to real-time web search results. Use the provided search results to give accurate, up-to-date answers. Always cite your sources with URLs.",
    "deep_research":  "You are a deep research expert. You have access to multiple search sources. Synthesize the information into a comprehensive, well-structured, cited report. Use headers, bullet points, and clear organization.",
    "translator":     "You are a professional translator fluent in 100+ languages. Detect the source language automatically and translate accurately, preserving tone, nuance, and meaning. If asked for a specific target language, use that language.",
    "summarizer":     "You are a world-class summarization expert. Create concise, accurate summaries that capture the most important points, key insights, and main conclusions. Structure your summary clearly.",
    "rewrite":        "You are a professional editor and ghostwriter. Rewrite the provided text to improve clarity, flow, engagement, and quality while preserving the original meaning and intent. Make it compelling and polished.",
    "grammar":        "You are a grammar, spelling, and style expert. Carefully identify and fix all errors in the provided text. Present the corrected version clearly, and optionally explain the key corrections made.",
    "explain_code":   "You are a senior software engineer and educator. Explain the provided code in clear, simple terms. Describe what it does, how it works, the design patterns used, potential issues, and how it could be improved.",
    "code_assistant": "You are an expert software engineer. Write clean, efficient, well-commented, production-ready code. Follow best practices, handle edge cases, and explain your implementation clearly.",
    "math_solver":    "You are a mathematics expert. Solve the problem step-by-step, showing all working clearly. Explain each step so the user can understand the process. Check your answer at the end.",
    "pdf_chat":       "You are a document analysis expert. The user has provided content from a document. Answer their questions accurately and comprehensively based on the document content provided.",
    "url_reader":     "You are a web content analyst. The user has provided content extracted from a URL. Analyze it thoroughly and answer their questions based on what you've read.",
    "image_analysis": "You are a computer vision and image analysis expert. Describe and analyze the provided image in detail. Identify objects, text, colors, patterns, composition, and any other relevant details.",
}

DEFAULT_SYSTEM_PROMPT = (
    "You are Bloxy-bot AI, a highly intelligent, helpful, and versatile AI assistant. "
    "You can help with coding, writing, research, math, analysis, creative tasks, and much more. "
    "You are honest about uncertainty and always strive to give accurate, helpful responses. "
    "Be concise when appropriate and detailed when needed. Today's date is {date}."
)

# =============================================================
# AI STREAMING ENGINE
# =============================================================

async def stream_openai_compat(
    messages: List[Dict],
    model: str,
    provider: str,
    api_key: str,
    base_url: str,
    max_tokens: int,
    temperature: float,
    extra_headers: Optional[Dict] = None,
) -> AsyncGenerator[str, None]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)

    payload = {
        "model":       model,
        "messages":    messages,
        "max_tokens":  max_tokens,
        "temperature": temperature,
        "stream":      True,
    }

    start    = time.time()
    tokens   = 0
    status_s = "success"

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
            ) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    err  = body.decode(errors="replace")
                    raise HTTPException(status_code=resp.status_code, detail=err[:500])

                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data = line[6:].strip()
                    if data == "[DONE]":
                        yield "data: [DONE]\n\n"
                        break
                    try:
                        obj   = json.loads(data)
                        delta = obj.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if delta:
                            tokens += count_tokens_approx(delta)
                            yield f"data: {json.dumps({'choices': [{'delta': {'content': delta}}]})}\n\n"
                        usage = obj.get("usage", {})
                        if usage.get("total_tokens"):
                            tokens = usage["total_tokens"]
                    except (json.JSONDecodeError, KeyError):
                        continue
    except HTTPException:
        status_s = "error"
        raise
    except Exception as e:
        status_s = "error"
        _log_error_internal(f"Stream error ({provider}/{model}): {e}", traceback.format_exc())
        raise HTTPException(status_code=502, detail=f"AI provider error: {str(e)[:200]}")
    finally:
        latency = int((time.time() - start) * 1000)
        _log_api_usage_internal(provider, model, tokens, latency, status_s)


async def stream_claude(
    messages: List[Dict],
    model: str,
    api_key: str,
    max_tokens: int,
    temperature: float,
    system_prompt: str,
) -> AsyncGenerator[str, None]:
    headers = {
        "x-api-key":         api_key,
        "anthropic-version": "2023-06-01",
        "content-type":      "application/json",
    }

    claude_messages = [m for m in messages if m.get("role") in ("user", "assistant")]

    payload = {
        "model":       model,
        "max_tokens":  max_tokens,
        "stream":      True,
        "system":      system_prompt,
        "messages":    claude_messages,
    }

    start    = time.time()
    tokens   = 0
    status_s = "success"

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
            ) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    raise HTTPException(status_code=resp.status_code, detail=body.decode(errors="replace")[:500])

                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data = line[6:].strip()
                    if not data:
                        continue
                    try:
                        obj   = json.loads(data)
                        delta = obj.get("delta", {}).get("text", "")
                        if delta:
                            tokens += count_tokens_approx(delta)
                            yield f"data: {json.dumps({'choices': [{'delta': {'content': delta}}]})}\n\n"
                    except (json.JSONDecodeError, KeyError):
                        continue
    except HTTPException:
        status_s = "error"
        raise
    except Exception as e:
        status_s = "error"
        _log_error_internal(f"Claude stream error: {e}", traceback.format_exc())
        raise HTTPException(status_code=502, detail=f"Claude error: {str(e)[:200]}")
    finally:
        latency = int((time.time() - start) * 1000)
        _log_api_usage_internal("claude", model, tokens, latency, status_s)


async def stream_cohere(
    messages: List[Dict],
    model: str,
    api_key: str,
    max_tokens: int,
    temperature: float,
    system_prompt: str,
) -> AsyncGenerator[str, None]:
    chat_history = []
    user_message = ""

    for m in messages:
        if m["role"] == "user":
            user_message = str(m.get("content", ""))
        elif m["role"] == "assistant":
            chat_history.append({"role": "CHATBOT", "message": str(m.get("content", ""))})

    payload = {
        "model":        model if model.startswith("command") else "command-r-plus",
        "message":      user_message,
        "chat_history": chat_history,
        "preamble":     system_prompt,
        "stream":       True,
        "max_tokens":   max_tokens,
        "temperature":  temperature,
    }

    start    = time.time()
    tokens   = 0
    status_s = "success"

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                "https://api.cohere.ai/v1/chat",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
            ) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    raise HTTPException(status_code=resp.status_code, detail=body.decode(errors="replace")[:500])

                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        if obj.get("event_type") == "text-generation":
                            text = obj.get("text", "")
                            if text:
                                tokens += count_tokens_approx(text)
                                yield f"data: {json.dumps({'choices': [{'delta': {'content': text}}]})}\n\n"
                    except (json.JSONDecodeError, KeyError):
                        continue
    except HTTPException:
        status_s = "error"
        raise
    except Exception as e:
        status_s = "error"
        _log_error_internal(f"Cohere stream error: {e}", traceback.format_exc())
        raise HTTPException(status_code=502, detail=f"Cohere error: {str(e)[:200]}")
    finally:
        latency = int((time.time() - start) * 1000)
        _log_api_usage_internal("cohere", model, tokens, latency, status_s)


async def call_ai_stream(
    messages:      List[Dict],
    model:         str,
    provider:      str,
    max_tokens:    int = 4096,
    temperature:   float = 0.7,
    system_prompt: str = "",
    tool:          Optional[str] = None,
) -> AsyncGenerator[str, None]:
    cfg = PROVIDER_CONFIGS.get(provider)
    if not cfg:
        raise HTTPException(400, f"Unknown provider: {provider}")

    api_key = cfg["key"]()
    if not api_key:
        raise HTTPException(400, f"API key not configured for provider: {provider}")

    sys_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT.format(
        date=datetime.now().strftime("%B %d, %Y")
    )
    if tool and tool in TOOL_SYSTEM_PROMPTS:
        sys_prompt = TOOL_SYSTEM_PROMPTS[tool] + "\n\n" + sys_prompt

    provider_type = cfg.get("type", "openai_compat")

    if provider_type == "claude":
        async for chunk in stream_claude(messages, model, api_key, max_tokens, temperature, sys_prompt):
            yield chunk
        return

    if provider_type == "cohere":
        async for chunk in stream_cohere(messages, model, api_key, max_tokens, temperature, sys_prompt):
            yield chunk
        return

    all_messages = [{"role": "system", "content": sys_prompt}] + list(messages)

    extra_headers = {}
    if provider == "openrouter":
        extra_headers = {
            "HTTP-Referer": Config.BASE_URL,
            "X-Title":      "Bloxy-bot AI",
        }

    async for chunk in stream_openai_compat(
        all_messages, model, provider, api_key,
        cfg["base_url"], max_tokens, temperature, extra_headers
    ):
        yield chunk


async def call_ai_sync(
    messages:      List[Dict],
    model:         str,
    provider:      str,
    max_tokens:    int = 2048,
    temperature:   float = 0.7,
    system_prompt: str = "",
) -> str:
    content = ""
    async for chunk in call_ai_stream(messages, model, provider, max_tokens, temperature, system_prompt):
        if chunk.startswith("data: ") and "[DONE]" not in chunk:
            try:
                obj = json.loads(chunk[6:].strip())
                content += obj.get("choices", [{}])[0].get("delta", {}).get("content", "")
            except (json.JSONDecodeError, KeyError, IndexError):
                pass
    return content


# =============================================================
# INTEGRATION SERVICES
# =============================================================

class WebSearchService:
    @staticmethod
    async def tavily_search(query: str, max_results: int = 6, depth: str = "basic") -> dict:
        if not Config.TAVILY_API_KEY:
            raise HTTPException(400, "Tavily API key not configured.")
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key":      Config.TAVILY_API_KEY,
                    "query":        query,
                    "max_results":  max_results,
                    "search_depth": depth,
                    "include_answer": True,
                    "include_raw_content": False,
                },
            )
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    async def exa_search(query: str, num_results: int = 5) -> dict:
        if not Config.EXA_API_KEY:
            raise HTTPException(400, "Exa API key not configured.")
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.exa.ai/search",
                headers={"x-api-key": Config.EXA_API_KEY, "Content-Type": "application/json"},
                json={"query": query, "numResults": num_results, "useAutoprompt": True, "contents": {"text": True}},
            )
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    async def duckduckgo_search(query: str) -> dict:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"},
            )
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    async def firecrawl_scrape(url: str) -> dict:
        if not Config.FIRECRAWL_API_KEY:
            raise HTTPException(400, "Firecrawl API key not configured.")
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.firecrawl.dev/v0/scrape",
                headers={"Authorization": f"Bearer {Config.FIRECRAWL_API_KEY}", "Content-Type": "application/json"},
                json={"url": url, "pageOptions": {"onlyMainContent": True}},
            )
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    async def simple_fetch(url: str) -> str:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Bloxy-bot AI/1.0"})
            resp.raise_for_status()
            return resp.text[:8000]


class KnowledgeService:
    @staticmethod
    async def wikipedia_search(query: str) -> dict:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action":  "query",
                    "list":    "search",
                    "srsearch": query,
                    "format":  "json",
                    "srlimit": 3,
                    "srprop":  "snippet|titlesnippet",
                },
            )
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    async def wikipedia_summary(title: str) -> dict:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
            )
            if resp.status_code == 404:
                return {"error": f"No Wikipedia article found for '{title}'"}
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    async def wikidata_search(query: str) -> dict:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://www.wikidata.org/w/api.php",
                params={
                    "action":   "wbsearchentities",
                    "search":   query,
                    "language": "en",
                    "format":   "json",
                    "limit":    5,
                },
            )
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    async def dictionary_lookup(word: str) -> dict:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.parse.quote(word)}"
            )
            if resp.status_code == 404:
                return {"error": f"No definition found for '{word}'"}
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    async def open_library_search(query: str) -> dict:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://openlibrary.org/search.json",
                params={"q": query, "limit": 5, "fields": "title,author_name,first_publish_year,isbn,subject"},
            )
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    async def arxiv_search(query: str, max_results: int = 5) -> str:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(
                "https://export.arxiv.org/api/query",
                params={"search_query": f"all:{query}", "max_results": max_results, "sortBy": "relevance"},
            )
            resp.raise_for_status()
            return resp.text[:6000]

    @staticmethod
    async def hackernews_top() -> dict:
        async with httpx.AsyncClient(timeout=15) as client:
            ids_resp = await client.get("https://hacker-news.firebaseio.com/v0/topstories.json")
            ids = ids_resp.json()[:10]
            stories = []
            for sid in ids[:6]:
                try:
                    s = await client.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
                    stories.append(s.json())
                except Exception:
                    pass
            return {"stories": stories}


class WeatherService:
    @staticmethod
    async def get_weather(location: str) -> dict:
        if Config.OPENWEATHER_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(
                        "https://api.openweathermap.org/data/2.5/weather",
                        params={"q": location, "appid": Config.OPENWEATHER_API_KEY, "units": "metric"},
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        data["source"] = "openweathermap"
                        return data
            except Exception:
                pass
        return await WeatherService.get_weather_open_meteo(location)

    @staticmethod
    async def get_weather_open_meteo(location: str) -> dict:
        async with httpx.AsyncClient(timeout=15) as client:
            geo = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": location, "count": 1, "format": "json"},
            )
            geo.raise_for_status()
            geo_data = geo.json()
            if not geo_data.get("results"):
                return {"error": f"Location '{location}' not found."}
            loc = geo_data["results"][0]
            weather = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude":        loc["latitude"],
                    "longitude":       loc["longitude"],
                    "current_weather": True,
                    "hourly":          "temperature_2m,precipitation_probability,windspeed_10m,weathercode",
                    "forecast_days":   3,
                    "timezone":        "auto",
                },
            )
            weather.raise_for_status()
            data = weather.json()
            data["location_name"] = loc.get("name", location)
            data["country"]       = loc.get("country", "")
            data["source"]        = "open-meteo"
            return data

    @staticmethod
    async def get_forecast(location: str, days: int = 7) -> dict:
        if Config.TOMORROW_IO_KEY:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(
                        "https://api.tomorrow.io/v4/weather/forecast",
                        params={"location": location, "apikey": Config.TOMORROW_IO_KEY},
                    )
                    if resp.status_code == 200:
                        return resp.json()
            except Exception:
                pass
        async with httpx.AsyncClient(timeout=15) as client:
            geo = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": location, "count": 1, "format": "json"},
            )
            geo_data = geo.json()
            if not geo_data.get("results"):
                return {"error": f"Location '{location}' not found."}
            loc = geo_data["results"][0]
            resp = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude":  loc["latitude"],
                    "longitude": loc["longitude"],
                    "daily":     "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
                    "forecast_days": min(days, 16),
                    "timezone":  "auto",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            data["location_name"] = loc.get("name", location)
            return data


class NewsService:
    @staticmethod
    async def get_news(query: str = "", category: str = "general", country: str = "us", page_size: int = 8) -> dict:
        if Config.NEWS_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    if query:
                        resp = await client.get(
                            "https://newsapi.org/v2/everything",
                            params={"q": query, "apiKey": Config.NEWS_API_KEY, "language": "en", "pageSize": page_size, "sortBy": "relevancy"},
                        )
                    else:
                        resp = await client.get(
                            "https://newsapi.org/v2/top-headlines",
                            params={"category": category, "country": country, "apiKey": Config.NEWS_API_KEY, "pageSize": page_size},
                        )
                    if resp.status_code == 200:
                        return resp.json()
            except Exception:
                pass

        if Config.GNEWS_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(
                        "https://gnews.io/api/v4/search" if query else "https://gnews.io/api/v4/top-headlines",
                        params={"q": query or category, "apikey": Config.GNEWS_API_KEY, "lang": "en", "max": page_size},
                    )
                    if resp.status_code == 200:
                        return resp.json()
            except Exception:
                pass

        if Config.GUARDIAN_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(
                        "https://content.guardianapis.com/search",
                        params={"q": query or category, "api-key": Config.GUARDIAN_API_KEY, "show-fields": "headline,trailText,thumbnail", "page-size": page_size},
                    )
                    if resp.status_code == 200:
                        return resp.json()
            except Exception:
                pass

        hn = await KnowledgeService.hackernews_top()
        articles = [{"title": s.get("title"), "url": s.get("url"), "source": {"name": "Hacker News"}, "publishedAt": str(s.get("time", ""))} for s in hn.get("stories", [])]
        return {"articles": articles, "source": "hackernews_fallback"}


class FinanceService:
    @staticmethod
    async def get_stock(symbol: str) -> dict:
        symbol = symbol.upper().strip()
        if Config.FINNHUB_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    quote   = await client.get(f"https://finnhub.io/api/v1/quote", params={"symbol": symbol, "token": Config.FINNHUB_API_KEY})
                    profile = await client.get(f"https://finnhub.io/api/v1/stock/profile2", params={"symbol": symbol, "token": Config.FINNHUB_API_KEY})
                    if quote.status_code == 200:
                        return {"symbol": symbol, "quote": quote.json(), "profile": profile.json() if profile.status_code == 200 else {}, "source": "finnhub"}
            except Exception:
                pass

        if Config.ALPHA_VANTAGE_KEY:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(
                        "https://www.alphavantage.co/query",
                        params={"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": Config.ALPHA_VANTAGE_KEY},
                    )
                    if resp.status_code == 200:
                        return {"symbol": symbol, "data": resp.json(), "source": "alphavantage"}
            except Exception:
                pass

        if Config.TWELVEDATA_KEY:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(
                        "https://api.twelvedata.com/quote",
                        params={"symbol": symbol, "apikey": Config.TWELVEDATA_KEY},
                    )
                    if resp.status_code == 200:
                        return {"symbol": symbol, "data": resp.json(), "source": "twelvedata"}
            except Exception:
                pass

        return {"error": f"Could not fetch stock data for {symbol}. Finance API not configured."}

    @staticmethod
    async def get_crypto(coin: str) -> dict:
        params: dict = {"ids": coin.lower(), "vs_currencies": "usd,btc,eth", "include_market_cap": "true", "include_24hr_change": "true", "include_24hr_vol": "true"}
        if Config.COINGECKO_API_KEY:
            params["x_cg_demo_api_key"] = Config.COINGECKO_API_KEY
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get("https://api.coingecko.com/api/v3/simple/price", params=params)
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    async def get_exchange_rates(base: str = "USD") -> dict:
        if Config.EXCHANGERATE_KEY:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(f"https://v6.exchangerate-api.com/v6/{Config.EXCHANGERATE_KEY}/latest/{base}")
                    if resp.status_code == 200:
                        return resp.json()
            except Exception:
                pass
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get("https://api.frankfurter.app/latest", params={"from": base})
            resp.raise_for_status()
            data = resp.json()
            data["source"] = "frankfurter"
            return data

    @staticmethod
    async def get_crypto_list(limit: int = 20) -> dict:
        params: dict = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": limit, "page": 1, "sparkline": False}
        if Config.COINGECKO_API_KEY:
            params["x_cg_demo_api_key"] = Config.COINGECKO_API_KEY
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get("https://api.coingecko.com/api/v3/coins/markets", params=params)
            resp.raise_for_status()
            return {"coins": resp.json()}


class SportsService:
    @staticmethod
    async def get_scores(sport: str = "soccer", league: str = "") -> dict:
        if Config.THESPORTSDB_KEY:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(
                        f"https://www.thesportsdb.com/api/v1/json/{Config.THESPORTSDB_KEY}/eventspastleague.php",
                        params={"id": "4328"},
                    )
                    if resp.status_code == 200:
                        return resp.json()
            except Exception:
                pass

        if Config.APISPORTS_KEY:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(
                        "https://v3.football.api-sports.io/fixtures",
                        headers={"x-apisports-key": Config.APISPORTS_KEY},
                        params={"live": "all"},
                    )
                    if resp.status_code == 200:
                        return resp.json()
            except Exception:
                pass

        if Config.ODDS_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(
                        f"https://api.the-odds-api.com/v4/sports/{sport}/odds",
                        params={"apiKey": Config.ODDS_API_KEY, "regions": "us", "markets": "h2h"},
                    )
                    if resp.status_code == 200:
                        return resp.json()
            except Exception:
                pass

        return {"error": "Sports data temporarily unavailable. Please try again later."}

    @staticmethod
    async def get_team_info(team: str) -> dict:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"https://www.thesportsdb.com/api/v1/json/{Config.THESPORTSDB_KEY}/searchteams.php",
                params={"t": team},
            )
            if resp.status_code == 200:
                return resp.json()
            return {"error": f"Team '{team}' not found."}


class EntertainmentService:
    @staticmethod
    async def search_movies(query: str, media_type: str = "movie") -> dict:
        if Config.TMDB_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(
                        f"https://api.themoviedb.org/3/search/{media_type}",
                        params={"api_key": Config.TMDB_API_KEY, "query": query, "language": "en-US", "page": 1},
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        data["source"] = "tmdb"
                        return data
            except Exception:
                pass

        if Config.OMDB_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(
                        "http://www.omdbapi.com/",
                        params={"apikey": Config.OMDB_API_KEY, "s": query, "type": media_type},
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        data["source"] = "omdb"
                        return data
            except Exception:
                pass

        return {"error": "Movie/TV API not configured."}

    @staticmethod
    async def get_trending_movies() -> dict:
        if not Config.TMDB_API_KEY:
            return {"error": "TMDB API key not configured."}
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://api.themoviedb.org/3/trending/movie/week",
                params={"api_key": Config.TMDB_API_KEY},
            )
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    async def search_tv_shows(query: str) -> dict:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get("https://api.tvmaze.com/search/shows", params={"q": query})
            resp.raise_for_status()
            return {"results": resp.json(), "source": "tvmaze"}

    @staticmethod
    async def get_anime(query: str) -> dict:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get("https://api.jikan.moe/v4/anime", params={"q": query, "limit": 5})
            if resp.status_code == 200:
                return resp.json()
            return {"error": "Anime search failed."}

    @staticmethod
    async def get_pokemon(name: str) -> dict:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"https://pokeapi.co/api/v2/pokemon/{name.lower()}")
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "name":   data["name"],
                    "id":     data["id"],
                    "types":  [t["type"]["name"] for t in data.get("types", [])],
                    "stats":  {s["stat"]["name"]: s["base_stat"] for s in data.get("stats", [])},
                    "height": data.get("height"),
                    "weight": data.get("weight"),
                    "abilities": [a["ability"]["name"] for a in data.get("abilities", [])],
                }
            return {"error": f"Pokemon '{name}' not found."}


class GeoService:
    @staticmethod
    async def get_country_info(country: str) -> dict:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"https://restcountries.com/v3.1/name/{urllib.parse.quote(country)}")
            if resp.status_code == 200:
                return resp.json()
            return {"error": f"Country '{country}' not found."}

    @staticmethod
    async def get_ip_info(ip: str = "") -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"http://ip-api.com/json/{ip}" if ip else "http://ip-api.com/json/"
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    async def geocode(location: str) -> dict:
        if Config.GEOAPIFY_KEY:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(
                        "https://api.geoapify.com/v1/geocode/search",
                        params={"text": location, "apiKey": Config.GEOAPIFY_KEY},
                    )
                    if resp.status_code == 200:
                        return resp.json()
            except Exception:
                pass
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": location, "format": "json", "limit": 3},
                headers={"User-Agent": "Bloxy-bot AI/1.0"},
            )
            resp.raise_for_status()
            return {"results": resp.json(), "source": "nominatim"}

    @staticmethod
    async def get_timezone(location: str) -> dict:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"http://worldtimeapi.org/api/timezone/{urllib.parse.quote(location)}")
            if resp.status_code == 200:
                return resp.json()
            resp2 = await client.get("http://worldtimeapi.org/api/timezone")
            return {"available_timezones": resp2.json() if resp2.status_code == 200 else [], "error": f"Timezone '{location}' not found."}


class MathService:
    @staticmethod
    async def wolfram_query(query: str) -> dict:
        if not Config.WOLFRAM_APP_ID:
            return {"error": "Wolfram Alpha not configured."}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                "http://api.wolframalpha.com/v2/query",
                params={"input": query, "appid": Config.WOLFRAM_APP_ID, "output": "json", "format": "plaintext"},
            )
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    def solve_basic(expression: str) -> dict:
        try:
            import sympy
            expr   = sympy.sympify(expression)
            result = sympy.simplify(expr)
            return {"expression": expression, "result": str(result), "latex": sympy.latex(result)}
        except Exception as e:
            return {"error": f"Could not solve: {str(e)}"}


class FoodService:
    @staticmethod
    async def search_food(query: str) -> dict:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://world.openfoodfacts.org/cgi/search.pl",
                params={"search_terms": query, "search_simple": 1, "action": "process", "json": 1, "page_size": 5},
            )
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    async def get_food_by_barcode(barcode: str) -> dict:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json")
            resp.raise_for_status()
            return resp.json()


class EmailService:
    @staticmethod
    async def send_email(to: str, subject: str, html: str):
        if not Config.RESEND_API_KEY:
            logger.warning(f"[EmailService] RESEND not configured. Would send to {to}: {subject}")
            return
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {Config.RESEND_API_KEY}", "Content-Type": "application/json"},
                json={"from": "Bloxy-bot AI <noreply@bloxybot.ai>", "to": [to], "subject": subject, "html": html},
            )
            if resp.status_code not in (200, 201):
                logger.error(f"[EmailService] Failed to send email: {resp.text}")

    @staticmethod
    async def send_password_reset(email: str, token: str):
        reset_url = f"{Config.BASE_URL}/reset-password?token={token}"
        html = f"""
        <div style="font-family:Inter,sans-serif;max-width:520px;margin:0 auto;padding:32px;background:#0f0f0f;color:#e5e5e5;border-radius:12px;">
          <div style="margin-bottom:20px;">
            <span style="font-size:24px;font-weight:700;color:#f97316;">Bloxy-bot AI</span>
          </div>
          <h2 style="color:#e5e5e5;margin-bottom:12px;">Reset your password</h2>
          <p style="color:#a3a3a3;margin-bottom:24px;">Click the button below to reset your password. This link expires in 24 hours.</p>
          <a href="{reset_url}" style="display:inline-block;background:#f97316;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;font-size:15px;">Reset Password</a>
          <p style="margin-top:24px;font-size:12px;color:#666;">If you didn't request this, safely ignore this email. Your password won't change.</p>
          <hr style="border:none;border-top:1px solid #2a2a2a;margin:24px 0;">
          <p style="font-size:11px;color:#444;">Bloxy-bot AI · Powered by advanced AI models</p>
        </div>"""
        await EmailService.send_email(email, "Reset your Bloxy-bot AI password", html)

    @staticmethod
    async def send_welcome_email(email: str, name: str):
        html = f"""
        <div style="font-family:Inter,sans-serif;max-width:520px;margin:0 auto;padding:32px;background:#0f0f0f;color:#e5e5e5;border-radius:12px;">
          <div style="margin-bottom:20px;">
            <span style="font-size:24px;font-weight:700;color:#f97316;">Bloxy-bot AI</span>
          </div>
          <h2 style="color:#e5e5e5;margin-bottom:12px;">Welcome, {name}! 🎉</h2>
          <p style="color:#a3a3a3;margin-bottom:16px;">Your account has been created successfully. You now have access to the most powerful AI models.</p>
          <ul style="color:#a3a3a3;padding-left:20px;margin-bottom:24px;">
            <li style="margin-bottom:8px;">Chat with GPT-4o, Claude, Llama, and more</li>
            <li style="margin-bottom:8px;">Real-time web search and deep research</li>
            <li style="margin-bottom:8px;">Weather, news, finance, sports and more</li>
            <li style="margin-bottom:8px;">Code assistant, math solver, translator</li>
          </ul>
          <a href="{Config.BASE_URL}" style="display:inline-block;background:#f97316;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;font-size:15px;">Start Chatting</a>
        </div>"""
        await EmailService.send_email(email, "Welcome to Bloxy-bot AI!", html)


# =============================================================
# TOOL EXECUTOR
# =============================================================

async def execute_tool(
    tool:       str,
    user_input: str,
    messages:   List[Dict],
    model:      str,
    provider:   str,
    options:    dict = {},
) -> AsyncGenerator[str, None]:
    tool_context = ""

    try:
        if tool == "web_search":
            try:
                data    = await WebSearchService.tavily_search(user_input, max_results=6)
                results = data.get("results", [])
                answer  = data.get("answer", "")
                tool_context = f"## Web Search Results for: {user_input}\n\n"
                if answer:
                    tool_context += f"**Quick Answer:** {answer}\n\n"
                for i, r in enumerate(results, 1):
                    tool_context += f"**{i}. {r.get('title', 'No title')}**\n"
                    tool_context += f"URL: {r.get('url', '')}\n"
                    tool_context += f"{r.get('content', '')[:500]}\n\n"
            except Exception:
                ddg = await WebSearchService.duckduckgo_search(user_input)
                tool_context = f"## Search Results for: {user_input}\n\n"
                if ddg.get("Abstract"):
                    tool_context += f"{ddg['Abstract']}\n\nSource: {ddg.get('AbstractURL', '')}\n\n"
                for topic in ddg.get("RelatedTopics", [])[:5]:
                    if isinstance(topic, dict) and topic.get("Text"):
                        tool_context += f"- {topic['Text']}\n"

        elif tool == "deep_research":
            tool_context = f"## Deep Research Report: {user_input}\n\n"
            try:
                tavily = await WebSearchService.tavily_search(user_input, max_results=8, depth="advanced")
                tool_context += "### Primary Sources (Tavily)\n"
                for r in tavily.get("results", []):
                    tool_context += f"**{r.get('title')}**\n{r.get('content', '')[:600]}\nSource: {r.get('url', '')}\n\n"
            except Exception:
                pass
            try:
                exa = await WebSearchService.exa_search(user_input, num_results=5)
                tool_context += "\n### Neural Search Sources (Exa)\n"
                for r in exa.get("results", []):
                    tool_context += f"**{r.get('title')}**\n{r.get('text', '')[:400]}\nSource: {r.get('url', '')}\n\n"
            except Exception:
                pass
            try:
                wiki = await KnowledgeService.wikipedia_search(user_input)
                wiki_results = wiki.get("query", {}).get("search", [])
                if wiki_results:
                    tool_context += "\n### Wikipedia\n"
                    for w in wiki_results[:2]:
                        snippet = re.sub(r"<[^>]+>", "", w.get("snippet", ""))
                        tool_context += f"**{w.get('title')}**: {snippet}\n\n"
            except Exception:
                pass

        elif tool == "url_reader":
            url = user_input.strip()
            if not url.startswith("http"):
                url = "https://" + url
            try:
                data    = await WebSearchService.firecrawl_scrape(url)
                content = data.get("data", {}).get("markdown", data.get("data", {}).get("content", ""))
                tool_context = f"## Content from {url}\n\n{content[:5000]}"
            except Exception:
                try:
                    raw_text = await WebSearchService.simple_fetch(url)
                    import re as re_module
                    clean = re_module.sub(r"<[^>]+>", " ", raw_text)
                    clean = re_module.sub(r"\s+", " ", clean).strip()
                    tool_context = f"## Content from {url}\n\n{clean[:4000]}"
                except Exception as e:
                    tool_context = f"Could not read URL '{url}': {str(e)}"

        elif tool == "translator":
            target_lang = options.get("target_language", "English")
            tool_context = f"Translate the following text to {target_lang}. Auto-detect the source language:\n\n{user_input}"

        elif tool == "summarizer":
            if user_input.strip().startswith("http"):
                try:
                    data    = await WebSearchService.firecrawl_scrape(user_input.strip())
                    content = data.get("data", {}).get("markdown", "")
                    tool_context = f"Summarize this content from {user_input}:\n\n{content[:6000]}"
                except Exception:
                    tool_context = f"Summarize the following:\n\n{user_input}"
            else:
                tool_context = f"Summarize the following text concisely and accurately:\n\n{user_input}"

        elif tool == "rewrite":
            style = options.get("style", "professional and clear")
            tool_context = f"Rewrite the following text in a {style} style. Improve clarity, flow, and quality:\n\n{user_input}"

        elif tool == "grammar":
            tool_context = f"Fix all grammar, spelling, punctuation, and style errors in the following text. Show the corrected version:\n\n{user_input}"

        elif tool == "explain_code":
            lang = options.get("language", "")
            lang_hint = f" ({lang})" if lang else ""
            tool_context = f"Explain this{lang_hint} code in detail. Describe what it does, how it works, and any important patterns:\n\n```\n{user_input}\n```"

        elif tool == "code_assistant":
            tool_context = user_input

        elif tool == "math_solver":
            extra = ""
            if Config.WOLFRAM_APP_ID:
                try:
                    wolfram = await MathService.wolfram_query(user_input)
                    pods    = wolfram.get("queryresult", {}).get("pods", [])
                    if pods:
                        extra = "\n\nWolfram Alpha results:\n"
                        for pod in pods[:4]:
                            title = pod.get("title", "")
                            for sub in pod.get("subpods", []):
                                plaintext = sub.get("plaintext", "")
                                if plaintext:
                                    extra += f"**{title}**: {plaintext}\n"
                except Exception:
                    pass
            tool_context = f"Solve this math problem step-by-step, showing all working clearly:{extra}\n\nProblem: {user_input}"

        elif tool == "image_analysis":
            tool_context = user_input

        elif tool == "pdf_chat":
            tool_context = user_input

        else:
            tool_context = user_input

    except Exception as e:
        _log_error_internal(f"Tool execution error ({tool}): {str(e)}", traceback.format_exc())
        tool_context = f"[Note: Tool context retrieval failed: {str(e)}]\n\nUser query: {user_input}"

    augmented_messages = list(messages)
    if tool_context and tool_context != user_input:
        if augmented_messages and augmented_messages[-1].get("role") == "user":
            augmented_messages[-1] = {
                "role":    "user",
                "content": f"{tool_context}\n\n---\nUser query: {user_input}",
            }
        else:
            augmented_messages.append({"role": "user", "content": tool_context})

    async for chunk in call_ai_stream(augmented_messages, model, provider, tool=tool):
        yield chunk


# =============================================================
# PDF PROCESSING
# =============================================================

def extract_text_from_pdf(file_bytes: bytes) -> str:
    text = ""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages[:30]:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text[:15000]
    except ImportError:
        pass
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages[:30]:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text[:15000]
    except ImportError:
        pass
    return "[PDF text extraction unavailable — pdfplumber or pypdf not installed]"


# =============================================================
# APP FACTORY
# =============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    _log_system_internal("INFO", "Bloxy-bot AI started successfully.")
    yield
    _log_system_internal("INFO", "Bloxy-bot AI shutting down.")


app = FastAPI(
    title="Bloxy-bot AI",
    description="Production-ready AI chatbot backend",
    version="2.0.0",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# =============================================================
# FRONTEND ROUTES
# =============================================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request, token: str = ""):
    return templates.TemplateResponse(request=request, name="index.html")


# =============================================================
# AUTH ROUTES
# =============================================================

@app.post("/api/auth/register")
async def register(
    body:             RegisterRequest,
    response:         Response,
    background_tasks: BackgroundTasks,
    db:               Session = Depends(get_db),
):
    existing = db.query(User).filter(User.email == body.email.lower().strip()).first()
    if existing:
        raise HTTPException(400, "An account with this email already exists.")

    user = User(
        name=body.name.strip(),
        email=body.email.lower().strip(),
        password=hash_password(body.password),
        provider="email",
        role="admin" if body.email.lower().strip() in ADMIN_EMAILS else "user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_jwt(user.id, user.email)
    set_auth_cookie(response, token)
    background_tasks.add_task(EmailService.send_welcome_email, user.email, user.name)
    _log_system_internal("INFO", f"New user registered: {user.email}")
    return {"user": user_to_dict(user)}


@app.post("/api/auth/login")
async def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower().strip()).first()
    if not user or not user.password or not verify_password(body.password, user.password):
        raise HTTPException(401, "Invalid email or password.")
    if not user.is_active:
        raise HTTPException(403, "This account has been disabled.")
    token = create_jwt(user.id, user.email)
    set_auth_cookie(response, token, body.remember)
    _log_system_internal("INFO", f"User logged in: {user.email}")
    return {"user": user_to_dict(user)}


@app.post("/api/auth/logout")
async def logout(response: Response):
    response.delete_cookie(Config.SESSION_COOKIE)
    return {"message": "Logged out successfully."}


@app.get("/api/auth/me")
async def me(user: Optional[User] = Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated.")
    return {"user": user_to_dict(user)}


@app.post("/api/auth/forgot-password")
async def forgot_password(
    body:             ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db:               Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == body.email.lower().strip()).first()
    if user:
        token_str  = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        db.add(PasswordResetToken(user_id=user.id, token=token_str, expires_at=expires_at))
        db.commit()
        background_tasks.add_task(EmailService.send_password_reset, user.email, token_str)
    return {"message": "If that email is registered, a reset link has been sent."}


@app.post("/api/auth/reset-password")
async def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == body.token,
        PasswordResetToken.used == False,
        PasswordResetToken.expires_at > datetime.now(timezone.utc),
    ).first()
    if not reset_token:
        raise HTTPException(400, "Invalid or expired reset token.")
    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if not user:
        raise HTTPException(404, "User not found.")
    user.password    = hash_password(body.password)
    reset_token.used = True
    db.commit()
    _log_system_internal("INFO", f"Password reset for: {user.email}")
    return {"message": "Password reset successfully. Please log in."}


@app.patch("/api/auth/profile")
async def update_profile(
    body: UpdateProfileRequest,
    db:   Session = Depends(get_db),
    user: User = Depends(require_user),
):
    if body.name:
        user.name = body.name.strip()
        db.commit()
        db.refresh(user)
    return {"user": user_to_dict(user)}


# ── Google OAuth ──────────────────────────────────────────────
@app.get("/api/auth/google")
async def google_oauth():
    if not Config.GOOGLE_CLIENT_ID:
        raise HTTPException(400, "Google OAuth not configured.")
    params = urllib.parse.urlencode({
        "client_id":     Config.GOOGLE_CLIENT_ID,
        "redirect_uri":  f"{Config.BASE_URL}/api/auth/google/callback",
        "response_type": "code",
        "scope":         "openid email profile",
        "access_type":   "offline",
        "prompt":        "select_account",
    })
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{params}")


@app.get("/api/auth/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    if not Config.GOOGLE_CLIENT_ID:
        return RedirectResponse("/?error=oauth_not_configured")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code":          code,
                    "client_id":     Config.GOOGLE_CLIENT_ID,
                    "client_secret": Config.GOOGLE_CLIENT_SECRET,
                    "redirect_uri":  f"{Config.BASE_URL}/api/auth/google/callback",
                    "grant_type":    "authorization_code",
                },
            )
            token_data  = token_resp.json()
            access_token = token_data.get("access_token", "")
            user_resp   = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_info = user_resp.json()

        email       = user_info.get("email", "").lower()
        name        = user_info.get("name", email.split("@")[0])
        provider_id = user_info.get("id", "")

        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                name=name, email=email, provider="google",
                provider_id=provider_id,
                role="admin" if email in ADMIN_EMAILS else "user",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        token    = create_jwt(user.id, user.email)
        redirect = RedirectResponse(url="/")
        set_auth_cookie(redirect, token)
        return redirect
    except Exception as e:
        _log_error_internal(f"Google OAuth error: {e}", traceback.format_exc())
        return RedirectResponse("/?error=google_auth_failed")


# ── GitHub OAuth ──────────────────────────────────────────────
@app.get("/api/auth/github")
async def github_oauth():
    if not Config.GITHUB_CLIENT_ID:
        raise HTTPException(400, "GitHub OAuth not configured.")
    params = urllib.parse.urlencode({
        "client_id":    Config.GITHUB_CLIENT_ID,
        "redirect_uri": f"{Config.BASE_URL}/api/auth/github/callback",
        "scope":        "user:email",
    })
    return RedirectResponse(f"https://github.com/login/oauth/authorize?{params}")


@app.get("/api/auth/github/callback")
async def github_callback(code: str, db: Session = Depends(get_db)):
    if not Config.GITHUB_CLIENT_ID:
        return RedirectResponse("/?error=oauth_not_configured")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            token_resp = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={"client_id": Config.GITHUB_CLIENT_ID, "client_secret": Config.GITHUB_CLIENT_SECRET, "code": code},
            )
            token_data   = token_resp.json()
            access_token = token_data.get("access_token", "")

            user_resp    = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            )
            user_info = user_resp.json()

            emails_resp = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            )
            emails = emails_resp.json() if emails_resp.status_code == 200 else []

        primary_email = next(
            (e["email"] for e in emails if isinstance(e, dict) and e.get("primary") and e.get("verified")),
            user_info.get("email") or f"{user_info.get('login', 'user')}@github.local",
        )
        primary_email = primary_email.lower()
        name          = user_info.get("name") or user_info.get("login", "GitHub User")
        provider_id   = str(user_info.get("id", ""))

        user = db.query(User).filter(User.email == primary_email).first()
        if not user:
            user = User(
                name=name, email=primary_email, provider="github",
                provider_id=provider_id,
                role="admin" if primary_email in ADMIN_EMAILS else "user",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        token    = create_jwt(user.id, user.email)
        redirect = RedirectResponse(url="/")
        set_auth_cookie(redirect, token)
        return redirect
    except Exception as e:
        _log_error_internal(f"GitHub OAuth error: {e}", traceback.format_exc())
        return RedirectResponse("/?error=github_auth_failed")


# =============================================================
# CHAT ROUTE
# =============================================================

@app.post("/api/chat")
async def chat(
    request:      Request,
    db:           Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    content_type = request.headers.get("content-type", "")
    file_content: Optional[str] = None
    file_name:    Optional[str] = None
    body_data:    dict          = {}

    if "multipart/form-data" in content_type:
        form      = await request.form()
        body_data = json.loads(form.get("data", "{}"))
        file      = form.get("file")
        if file and hasattr(file, "read"):
            file_bytes = await file.read()
            file_name  = getattr(file, "filename", "uploaded_file")
            mime       = getattr(file, "content_type", "") or ""
            if "pdf" in mime or file_name.endswith(".pdf"):
                file_content = extract_text_from_pdf(file_bytes)
            elif "image" in mime:
                b64          = base64.b64encode(file_bytes).decode()
                file_content = f"[IMAGE_DATA:{mime}:{b64}]"
            else:
                file_content = file_bytes.decode("utf-8", errors="replace")[:6000]
    else:
        raw_body  = await request.body()
        body_data = json.loads(raw_body)

    body = ChatRequest(**body_data)

    messages = list(body.messages)

    if file_content and messages:
        last_msg = messages[-1]
        if "[IMAGE_DATA:" in file_content:
            parts    = file_content[12:].split(":", 1)
            mime_    = parts[0]
            b64_data = parts[1] if len(parts) > 1 else ""
            messages[-1] = {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{mime_};base64,{b64_data}"}},
                    {"type": "text", "text": str(last_msg.get("content", ""))},
                ],
            }
        else:
            messages[-1] = {
                "role":    "user",
                "content": f"[File: {file_name}]\n\n{file_content}\n\n---\n{str(last_msg.get('content', ''))}",
            }

    if current_user and messages:
        try:
            last_content = messages[-1].get("content", "")
            if isinstance(last_content, list):
                last_content = "Image Analysis"
            else:
                last_content = str(last_content)

            if not body.chat_id:
                chat_obj = Chat(
                    user_id=current_user.id,
                    title=last_content[:80],
                    model=body.model,
                    provider=body.provider,
                )
                db.add(chat_obj)
                db.commit()
                chat_id = chat_obj.id
            else:
                chat_id = body.chat_id

            for msg in messages[-2:]:
                role    = msg.get("role", "user")
                content = msg.get("content", "")
                if isinstance(content, list):
                    content = "[multipart content]"
                db.add(Message(
                    chat_id=chat_id,
                    role=role,
                    content=str(content)[:10000],
                    model=body.model,
                ))
            db.commit()
        except Exception as e:
            _log_error_internal(f"Chat DB save error: {e}")

    async def stream_generator():
        try:
            if body.tool:
                user_input = messages[-1].get("content", "") if messages else ""
                if isinstance(user_input, list):
                    user_input = next(
                        (c.get("text", "") for c in user_input if isinstance(c, dict) and c.get("type") == "text"),
                        "",
                    )
                async for chunk in execute_tool(
                    body.tool, str(user_input), messages[:-1],
                    body.model, body.provider, {}
                ):
                    yield chunk
            elif body.web_search and messages:
                user_input = messages[-1].get("content", "")
                if isinstance(user_input, list):
                    user_input = next(
                        (c.get("text", "") for c in user_input if isinstance(c, dict) and c.get("type") == "text"),
                        "",
                    )
                async for chunk in execute_tool(
                    "web_search", str(user_input), messages[:-1],
                    body.model, body.provider, {}
                ):
                    yield chunk
            else:
                async for chunk in call_ai_stream(
                    messages, body.model, body.provider,
                    body.max_tokens, body.temperature,
                    body.system_prompt or "",
                ):
                    yield chunk
        except HTTPException as e:
            yield f"data: {json.dumps({'error': e.detail})}\n\n"
        except Exception as e:
            _log_error_internal(f"Stream error: {e}", traceback.format_exc())
            yield f"data: {json.dumps({'error': 'An error occurred. Please try again.'})}\n\n"

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# =============================================================
# TOOL / INTEGRATION ROUTES
# =============================================================

@app.get("/api/tools/weather")
async def weather_route(location: str):
    try:
        return await WeatherService.get_weather(location)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/tools/weather/forecast")
async def weather_forecast_route(location: str, days: int = 7):
    try:
        return await WeatherService.get_forecast(location, days)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/tools/news")
async def news_route(q: str = "", category: str = "general", country: str = "us"):
    try:
        return await NewsService.get_news(q, category, country)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/tools/stock")
async def stock_route(symbol: str):
    try:
        return await FinanceService.get_stock(symbol)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/tools/crypto")
async def crypto_route(coin: str):
    try:
        return await FinanceService.get_crypto(coin)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/tools/crypto/list")
async def crypto_list_route(limit: int = 20):
    try:
        return await FinanceService.get_crypto_list(limit)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/tools/exchange")
async def exchange_route(base: str = "USD"):
    try:
        return await FinanceService.get_exchange_rates(base)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/tools/sports")
async def sports_route(sport: str = "soccer", league: str = ""):
    try:
        return await SportsService.get_scores(sport, league)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/tools/sports/team")
async def sports_team_route(team: str):
    try:
        return await SportsService.get_team_info(team)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/tools/movies")
async def movies_route(q: str, type: str = "movie"):
    try:
        return await EntertainmentService.search_movies(q, type)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/tools/movies/trending")
async def movies_trending_route():
    try:
        return await EntertainmentService.get_trending_movies()
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/tools/tvshows")
async def tvshows_route(q: str):
    try:
        return await EntertainmentService.search_tv_shows(q)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/tools/anime")
async def anime_route(q: str):
    try:
        return await EntertainmentService.get_anime(q)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/tools/pokemon")
async def pokemon_route(name: str):
    try:
        return await EntertainmentService.get_pokemon(name)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/tools/wikipedia")
async def wikipedia_route(q: str):
    try:
        return await KnowledgeService.wikipedia_summary(q)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/tools/wikipedia/search")
async def wikipedia_search_route(q: str):
    try:
        return await KnowledgeService.wikipedia_search(q)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/tools/wikidata")
async def wikidata_route(q: str):
    try:
        return await KnowledgeService.wikidata_search(q)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/tools/dictionary")
async def dictionary_route(word: str):
    try:
        return await KnowledgeService.dictionary_lookup(word)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/tools/books")
async def books_route(q: str):
    try:
        return await KnowledgeService.open_library_search(q)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/tools/arxiv")
async def arxiv_route(q: str):
    try:
        raw = await KnowledgeService.arxiv_search(q)
        return {"raw": raw, "query": q}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/tools/hackernews")
async def hn_route():
    try:
        return await KnowledgeService.hackernews_top()
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/tools/country")
async def country_route(name: str):
    try:
        return await GeoService.get_country_info(name)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/tools/ip")
async def ip_route(ip: str = ""):
    try:
        return await GeoService.get_ip_info(ip)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/tools/geocode")
async def geocode_route(location: str):
    try:
        return await GeoService.geocode(location)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/tools/timezone")
async def timezone_route(location: str):
    try:
        return await GeoService.get_timezone(location)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/tools/food")
async def food_route(q: str):
    try:
        return await FoodService.search_food(q)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/tools/food/barcode")
async def food_barcode_route(barcode: str):
    try:
        return await FoodService.get_food_by_barcode(barcode)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/tools/search")
async def search_route(body: ToolRequest):
    try:
        if Config.TAVILY_API_KEY:
            return await WebSearchService.tavily_search(body.input)
        return await WebSearchService.duckduckgo_search(body.input)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/tools/deep-research")
async def deep_research_route(body: ToolRequest):
    try:
        results: dict = {}
        if Config.TAVILY_API_KEY:
            results["tavily"] = await WebSearchService.tavily_search(body.input, max_results=8, depth="advanced")
        if Config.EXA_API_KEY:
            try:
                results["exa"] = await WebSearchService.exa_search(body.input, num_results=6)
            except Exception:
                pass
        results["wikipedia"] = await KnowledgeService.wikipedia_search(body.input)
        results["duckduckgo"] = await WebSearchService.duckduckgo_search(body.input)
        return results
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/tools/url-reader")
async def url_reader_route(url: str):
    try:
        if Config.FIRECRAWL_API_KEY:
            data    = await WebSearchService.firecrawl_scrape(url)
            content = data.get("data", {}).get("markdown", "")
            return {"url": url, "content": content[:8000], "source": "firecrawl"}
        content = await WebSearchService.simple_fetch(url)
        return {"url": url, "content": content, "source": "direct"}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/tools/math")
async def math_route(q: str):
    try:
        if Config.WOLFRAM_APP_ID:
            return await MathService.wolfram_query(q)
        return MathService.solve_basic(q)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/tools/duckduckgo")
async def ddg_route(q: str):
    try:
        return await WebSearchService.duckduckgo_search(q)
    except Exception as e:
        raise HTTPException(500, str(e))


# =============================================================
# ADMIN ROUTES
# =============================================================

@app.get("/api/admin/stats")
async def admin_stats(
    admin: User    = Depends(require_admin),
    db:    Session = Depends(get_db),
):
    try:
        today       = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday   = today - timedelta(days=1)
        last_24h    = datetime.now(timezone.utc) - timedelta(hours=24)

        total_users      = db.query(func.count(User.id)).scalar() or 0
        users_today      = db.query(func.count(User.id)).filter(User.created_at >= today).scalar() or 0
        total_chats      = db.query(func.count(Chat.id)).scalar() or 0
        chats_today      = db.query(func.count(Chat.id)).filter(Chat.created_at >= today).scalar() or 0
        messages_today   = db.query(func.count(Message.id)).filter(Message.created_at >= today).scalar() or 0
        messages_yest    = db.query(func.count(Message.id)).filter(Message.created_at >= yesterday, Message.created_at < today).scalar() or 0
        api_calls_today  = db.query(func.count(ApiUsageLog.id)).filter(ApiUsageLog.created_at >= today).scalar() or 0
        errors_24h       = db.query(func.count(ErrorLog.id)).filter(ErrorLog.created_at >= last_24h).scalar() or 0
        total_tokens_day = db.query(func.sum(ApiUsageLog.tokens)).filter(ApiUsageLog.created_at >= today).scalar() or 0

        return {
            "total_users":      total_users,
            "users_today":      users_today,
            "total_chats":      total_chats,
            "chats_today":      chats_today,
            "messages_today":   messages_today,
            "messages_yesterday": messages_yest,
            "api_calls_today":  api_calls_today,
            "errors_24h":       errors_24h,
            "active_sessions":  0,
            "total_tokens_today": total_tokens_day,
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/admin/users")
async def admin_users(
    admin: User    = Depends(require_admin),
    db:    Session = Depends(get_db),
    page:  int     = 1,
    limit: int     = 50,
):
    try:
        offset = (page - 1) * limit
        users  = db.query(User).order_by(User.created_at.desc()).offset(offset).limit(limit).all()
        total  = db.query(func.count(User.id)).scalar() or 0
        return {
            "users": [
                {
                    **user_to_dict(u),
                    "chat_count": db.query(func.count(Chat.id)).filter(Chat.user_id == u.id).scalar() or 0,
                    "is_active":  u.is_active,
                }
                for u in users
            ],
            "total": total,
            "page":  page,
            "pages": math.ceil(total / limit),
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@app.patch("/api/admin/users/{user_id}/toggle")
async def admin_toggle_user(
    user_id: str,
    admin:   User    = Depends(require_admin),
    db:      Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found.")
    if user.email in ADMIN_EMAILS:
        raise HTTPException(403, "Cannot disable admin accounts.")
    user.is_active = not user.is_active
    db.commit()
    _log_system_internal("INFO", f"Admin toggled user {user.email}: is_active={user.is_active}")
    return {"message": f"User {'enabled' if user.is_active else 'disabled'}.", "is_active": user.is_active}


@app.delete("/api/admin/users/{user_id}")
async def admin_delete_user(
    user_id: str,
    admin:   User    = Depends(require_admin),
    db:      Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found.")
    if user.email in ADMIN_EMAILS:
        raise HTTPException(403, "Cannot delete admin accounts.")
    db.delete(user)
    db.commit()
    _log_system_internal("INFO", f"Admin deleted user: {user.email}")
    return {"message": "User deleted."}


@app.get("/api/admin/chat-logs")
async def admin_chat_logs(
    admin: User    = Depends(require_admin),
    db:    Session = Depends(get_db),
    page:  int     = 1,
    limit: int     = 50,
):
    try:
        offset = (page - 1) * limit
        chats  = db.query(Chat).order_by(Chat.created_at.desc()).offset(offset).limit(limit).all()
        total  = db.query(func.count(Chat.id)).scalar() or 0
        logs   = []
        for c in chats:
            user_email = db.query(User.email).filter(User.id == c.user_id).scalar() if c.user_id else "Guest"
            msg_count  = db.query(func.count(Message.id)).filter(Message.chat_id == c.id).scalar() or 0
            logs.append({
                "id":            c.id,
                "user_email":    user_email or "Guest",
                "model":         c.model,
                "provider":      c.provider,
                "title":         c.title,
                "message_count": msg_count,
                "total_tokens":  c.total_tokens or 0,
                "created_at":    c.created_at.isoformat() if c.created_at else None,
            })
        return {"logs": logs, "total": total, "page": page, "pages": math.ceil(total / limit)}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/admin/api-usage")
async def admin_api_usage(
    admin: User    = Depends(require_admin),
    db:    Session = Depends(get_db),
):
    try:
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        logs  = db.query(ApiUsageLog).filter(ApiUsageLog.created_at >= today).all()
        by_provider: Dict[str, dict] = {}
        for log in logs:
            p = log.provider
            if p not in by_provider:
                by_provider[p] = {"requests": 0, "tokens": 0, "latencies": [], "errors": 0}
            by_provider[p]["requests"] += 1
            by_provider[p]["tokens"]   += log.tokens or 0
            if log.latency_ms:
                by_provider[p]["latencies"].append(log.latency_ms)
            if log.status == "error":
                by_provider[p]["errors"] += 1
        result = {}
        for p, d in by_provider.items():
            lats = d["latencies"]
            result[p] = {
                "requests":    d["requests"],
                "tokens":      d["tokens"],
                "avg_latency": int(sum(lats) / len(lats)) if lats else 0,
                "errors":      d["errors"],
                "credits_used": d["tokens"],
                "pages_crawled": d["requests"],
            }
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/admin/provider-status")
async def admin_provider_status(admin: User = Depends(require_admin)):
    checks = {
        "openai":     ("https://api.openai.com/v1/models",                  {"Authorization": f"Bearer {Config.OPENAI_API_KEY}"}),
        "groq":       ("https://api.groq.com/openai/v1/models",             {"Authorization": f"Bearer {Config.GROQ_API_KEY}"}),
        "openrouter": ("https://openrouter.ai/api/v1/models",               {"Authorization": f"Bearer {Config.OPENROUTER_API_KEY}"}),
        "kimi":       ("https://api.moonshot.cn/v1/models",                 {"Authorization": f"Bearer {Config.KIMI_API_KEY}"}),
        "deepseek":   ("https://api.deepseek.com/v1/models",                {"Authorization": f"Bearer {Config.DEEPSEEK_API_KEY}"}),
        "mistral":    ("https://api.mistral.ai/v1/models",                  {"Authorization": f"Bearer {Config.MISTRAL_API_KEY}"}),
        "claude":     ("https://api.anthropic.com/v1/models",               {"x-api-key": Config.CLAUDE_API_KEY, "anthropic-version": "2023-06-01"}),
        "tavily":     ("https://api.tavily.com/search",                     {}),
        "exa":        ("https://api.exa.ai/search",                         {}),
        "firecrawl":  ("https://api.firecrawl.dev/v0/scrape",               {}),
        "weather":    (f"https://api.openweathermap.org/data/2.5/weather?q=London&appid={Config.OPENWEATHER_API_KEY}", {}),
        "news":       (f"https://newsapi.org/v2/top-headlines?country=us&apiKey={Config.NEWS_API_KEY}&pageSize=1", {}),
        "finnhub":    (f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={Config.FINNHUB_API_KEY}", {}),
        "tmdb":       (f"https://api.themoviedb.org/3/configuration?api_key={Config.TMDB_API_KEY}", {}),
        "sports":     ("https://www.thesportsdb.com/api/v1/json/1/search_all_leagues.php?s=Soccer", {}),
    }
    results = {}
    async with httpx.AsyncClient(timeout=8) as client:
        for name, (url, headers) in checks.items():
            key_missing = (
                ("appid=" in url and url.endswith("=")) or
                ("apiKey=" in url and url.endswith("=")) or
                ("token=" in url and url.endswith("=")) or
                ("api_key=" in url and url.endswith("="))
            )
            if key_missing:
                results[name] = {"status": "not_configured", "latency": None}
                continue
            try:
                start = time.time()
                r     = await client.get(url, headers=headers)
                ms    = int((time.time() - start) * 1000)
                results[name] = {"status": "online" if r.status_code < 500 else "offline", "latency": ms}
            except Exception:
                results[name] = {"status": "offline", "latency": None}
    return results


@app.get("/api/admin/system-logs")
async def admin_system_logs(
    admin: User    = Depends(require_admin),
    db:    Session = Depends(get_db),
    limit: int     = 200,
):
    logs = db.query(SystemLog).order_by(SystemLog.created_at.desc()).limit(limit).all()
    return {
        "logs": [
            {"level": l.level, "message": l.message, "timestamp": l.created_at.isoformat()}
            for l in logs
        ]
    }


@app.get("/api/admin/error-logs")
async def admin_error_logs(
    admin: User    = Depends(require_admin),
    db:    Session = Depends(get_db),
    limit: int     = 200,
):
    logs = db.query(ErrorLog).order_by(ErrorLog.created_at.desc()).limit(limit).all()
    return {
        "logs": [
            {"message": l.message, "traceback": l.traceback, "timestamp": l.created_at.isoformat()}
            for l in logs
        ]
    }


@app.delete("/api/admin/logs/system")
async def admin_clear_system_logs(
    admin: User    = Depends(require_admin),
    db:    Session = Depends(get_db),
):
    db.query(SystemLog).delete()
    db.commit()
    return {"message": "System logs cleared."}


@app.delete("/api/admin/logs/errors")
async def admin_clear_error_logs(
    admin: User    = Depends(require_admin),
    db:    Session = Depends(get_db),
):
    db.query(ErrorLog).delete()
    db.commit()
    return {"message": "Error logs cleared."}


# =============================================================
# HEALTH & MISC ROUTES
# =============================================================

@app.get("/api/health")
async def health():
    return {
        "status":      "ok",
        "app":         "Bloxy-bot AI",
        "version":     "2.0.0",
        "timestamp":   datetime.now(timezone.utc).isoformat(),
        "environment": Config.ENVIRONMENT,
        "providers": {
            "openai":     bool(Config.OPENAI_API_KEY),
            "groq":       bool(Config.GROQ_API_KEY),
            "openrouter": bool(Config.OPENROUTER_API_KEY),
            "kimi":       bool(Config.KIMI_API_KEY),
            "deepseek":   bool(Config.DEEPSEEK_API_KEY),
            "mistral":    bool(Config.MISTRAL_API_KEY),
            "cohere":     bool(Config.COHERE_API_KEY),
            "claude":     bool(Config.CLAUDE_API_KEY),
        },
        "integrations": {
            "tavily":      bool(Config.TAVILY_API_KEY),
            "exa":         bool(Config.EXA_API_KEY),
            "firecrawl":   bool(Config.FIRECRAWL_API_KEY),
            "weather":     bool(Config.OPENWEATHER_API_KEY),
            "news":        bool(Config.NEWS_API_KEY),
            "finance":     bool(Config.FINNHUB_API_KEY),
            "tmdb":        bool(Config.TMDB_API_KEY),
            "wolfram":     bool(Config.WOLFRAM_APP_ID),
            "resend":      bool(Config.RESEND_API_KEY),
        },
    }


@app.get("/api/models")
async def list_models():
    return {
        "models": [
            {"id": "gpt-4o",                         "name": "GPT-4o",             "provider": "openai",      "available": bool(Config.OPENAI_API_KEY)},
            {"id": "gpt-4-turbo",                    "name": "GPT-4 Turbo",        "provider": "openai",      "available": bool(Config.OPENAI_API_KEY)},
            {"id": "gpt-3.5-turbo",                  "name": "GPT-3.5 Turbo",      "provider": "openai",      "available": bool(Config.OPENAI_API_KEY)},
            {"id": "claude-3-5-sonnet-20241022",      "name": "Claude 3.5 Sonnet",  "provider": "claude",      "available": bool(Config.CLAUDE_API_KEY)},
            {"id": "claude-3-opus-20240229",          "name": "Claude 3 Opus",      "provider": "claude",      "available": bool(Config.CLAUDE_API_KEY)},
            {"id": "llama-3.1-70b-versatile",        "name": "Llama 3.1 70B",      "provider": "groq",        "available": bool(Config.GROQ_API_KEY)},
            {"id": "mixtral-8x7b-32768",             "name": "Mixtral 8x7B",       "provider": "groq",        "available": bool(Config.GROQ_API_KEY)},
            {"id": "gemma2-9b-it",                   "name": "Gemma 2 9B",         "provider": "groq",        "available": bool(Config.GROQ_API_KEY)},
            {"id": "moonshot-v1-128k",               "name": "Moonshot 128K",      "provider": "kimi",        "available": bool(Config.KIMI_API_KEY)},
            {"id": "deepseek-chat",                  "name": "DeepSeek Chat",      "provider": "deepseek",    "available": bool(Config.DEEPSEEK_API_KEY)},
            {"id": "deepseek-coder",                 "name": "DeepSeek Coder",     "provider": "deepseek",    "available": bool(Config.DEEPSEEK_API_KEY)},
            {"id": "mistral-large-latest",           "name": "Mistral Large",      "provider": "mistral",     "available": bool(Config.MISTRAL_API_KEY)},
            {"id": "command-r-plus",                 "name": "Command R+",         "provider": "cohere",      "available": bool(Config.COHERE_API_KEY)},
            {"id": "anthropic/claude-3.5-sonnet",    "name": "Claude 3.5 Sonnet",  "provider": "openrouter",  "available": bool(Config.OPENROUTER_API_KEY)},
            {"id": "google/gemini-pro-1.5",          "name": "Gemini Pro 1.5",     "provider": "openrouter",  "available": bool(Config.OPENROUTER_API_KEY)},
            {"id": "meta-llama/llama-3.1-70b-instruct", "name": "Llama 3.1 70B", "provider": "openrouter",  "available": bool(Config.OPENROUTER_API_KEY)},
        ]
    }


# =============================================================
# ERROR HANDLERS
# =============================================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": "Endpoint not found."}, status_code=404)
    return templates.TemplateResponse(request=request, name="index.html", status_code=200)


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    _log_error_internal(f"500 on {request.url.path}: {str(exc)}", traceback.format_exc())
    return JSONResponse({"detail": "Internal server error."}, status_code=500)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


# =============================================================
# ENTRY POINT
# =============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=Config.ENVIRONMENT != "production",
        log_level="info",
        access_log=True,
    )
PYEOF
echo "Done. Lines: $(wc -l < /mnt/user-data/outputs/Bloxy-bot/app.py)"
Output

Command argument is 107_214 bytes, exceeding the 100_000-byte per-argument limit. For large content, pipe via stdin or use a file-write API instead of embedding the content inline in the command. Argument preview: "cat > /mnt/user-data/outputs/Bloxy-bot/app.py << 'PYEOF'\n# =============================================================\n#  BLOXY-BOT AI — app.py\n#  Complete Production FastAPI Backend\n#  Python 3.11 "
Done
