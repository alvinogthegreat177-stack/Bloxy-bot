# =============================================================
#  BLOXY-BOT AI — app.py
#  Complete FastAPI backend — all parts integrated
#  Production-ready · Render-compatible · Python 3.11
# =============================================================

from __future__ import annotations

import asyncio
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
    Cookie,
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
    FileResponse,
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr, Field, validator
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
    text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker

# =============================================================
# CONFIGURATION & ENVIRONMENT
# =============================================================

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("bloxy-bot")

# ── Admin emails ──────────────────────────────────────────────
ADMIN_EMAILS = {
    "alvinogthegreat177@gmail.com",
    "alvinogthegreat177@outlook.com",
}

# ── Environment variables ─────────────────────────────────────
class Config:
    # Core
    SECRET_KEY          = os.getenv("SECRET_KEY", secrets.token_hex(32))
    DATABASE_URL        = os.getenv("DATABASE_URL", "sqlite:///./bloxy_bot.db")
    ENVIRONMENT         = os.getenv("ENVIRONMENT", "production")
    BASE_URL            = os.getenv("BASE_URL", "http://localhost:8000")

    # AI Providers
    OPENAI_API_KEY      = os.getenv("OPENAI_API_KEY", "")
    OPENROUTER_API_KEY  = os.getenv("OPENROUTER_API_KEY", "")
    GROQ_API_KEY        = os.getenv("GROQ_API_KEY", "")
    KIMI_API_KEY        = os.getenv("KIMI_API_KEY", "")
    DEEPSEEK_API_KEY    = os.getenv("DEEPSEEK_API_KEY", "")
    MISTRAL_API_KEY     = os.getenv("MISTRAL_API_KEY", "")
    COHERE_API_KEY      = os.getenv("COHERE_API_KEY", "")
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
    CLAUDE_API_KEY      = os.getenv("CLAUDE_API_KEY", "")  # Anthropic direct

    # Search & Research
    TAVILY_API_KEY      = os.getenv("TAVILY_API_KEY", "")
    EXA_API_KEY         = os.getenv("EXA_API_KEY", "")
    FIRECRAWL_API_KEY   = os.getenv("FIRECRAWL_API_KEY", "")
    SEARCH_API_KEY      = os.getenv("SEARCH_API_KEY", os.getenv("SEARCH_API-KEY", ""))

    # News
    NEWS_API_KEY        = os.getenv("NEWS_API_KEY", "")
    GNEWS_API_KEY       = os.getenv("GNEWS_API_KEY", "")
    GUARDIAN_API_KEY    = os.getenv("GUARDIAN_API_KEY", "")
    MEDIASTACK_API_KEY  = os.getenv("MEDIASTACK_API_KEY", "")

    # Weather
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
    TOMORROW_IO_KEY     = os.getenv("TOMORROW.IO_API_KEY", "")

    # Finance
    ALPHA_VANTAGE_KEY   = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    FINNHUB_API_KEY     = os.getenv("FINNHUB_API_KEY", "")
    EXCHANGERATE_KEY    = os.getenv("EXCHANGERATE_API_KEY", "")
    EXCHANGERATE_HOST   = os.getenv("EXCHANGERATE.HOST_API_KEY", "")
    COINGECKO_API_KEY   = os.getenv("COINGECKO_API_KEY", "")
    TWELVEDATA_KEY      = os.getenv("TWELVEDATA_API_KEY", "")

    # Sports
    SPORTRADAR_KEY      = os.getenv("SPORTRADAR_API_KEY", "")
    SPORTMONK_KEY       = os.getenv("SPORTMONK_API_KEY", "")
    APISPORTS_KEY       = os.getenv("APISPORTS_API_KEY", "")
    THESPORTSDB_KEY     = os.getenv("THESPORTSDB_API_KEY", "123")
    ALLSPORTS_KEY       = os.getenv("ALLSPORTS_API_KEY", "")
    ODDS_API_KEY        = os.getenv("ODDS_API_KEY", "")

    # Entertainment
    TMDB_API_KEY        = os.getenv("TMDB_API_KEY", "")
    OMDB_API_KEY        = os.getenv("OMDB_API_KEY", "")

    # Location & Geo
    GEOAPIFY_KEY        = os.getenv("GEOAPIFY_API_KEY", "")
    IPINFO_KEY          = os.getenv("IPINFO.IO_API_KEY", "")
    RESTCOUNTRIES_KEY   = os.getenv("RESTCOUNTRIES_API_KEY", "")
    TIMEZONEDB_KEY      = os.getenv("TIMEZONEDB_API_KEY", "")
    WORLDTIME_KEY       = os.getenv("WORLDTIME_API_KEY", "")

    # Email & Misc
    RESEND_API_KEY      = os.getenv("RESEND_API_KEY", "")
    WOLFRAM_APP_ID      = os.getenv("WOLFRAM_APP_ID", "")
    RANDOM_API_KEY      = os.getenv("RANDOM_API_KEY", "")

    # OAuth
    GOOGLE_CLIENT_ID    = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET= os.getenv("GOOGLE_CLIENT_SECRET", "")
    GITHUB_CLIENT_ID    = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET= os.getenv("GITHUB_CLIENT_SECRET", "")

    # JWT
    JWT_ALGORITHM       = "HS256"
    JWT_EXPIRE_DAYS     = 30
    SESSION_COOKIE      = "bloxy_session"


# =============================================================
# DATABASE SETUP (SQLite / PostgreSQL)
# =============================================================

db_url = Config.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
engine = create_engine(db_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── DB Models ─────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"
    id         = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name       = Column(String, nullable=False)
    email      = Column(String, unique=True, nullable=False, index=True)
    password   = Column(String, nullable=True)
    provider   = Column(String, default="email")
    provider_id= Column(String, nullable=True)
    role       = Column(String, default="user")
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    chats      = relationship("Chat", back_populates="user", cascade="all, delete-orphan")
    sessions   = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")


class Chat(Base):
    __tablename__ = "chats"
    id           = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id      = Column(String, ForeignKey("users.id"), nullable=True)
    title        = Column(String, default="New Chat")
    model        = Column(String, default="gpt-4o")
    provider     = Column(String, default="openai")
    message_count= Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    created_at   = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at   = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user         = relationship("User", back_populates="chats")
    messages     = relationship("Message", back_populates="chat", cascade="all, delete-orphan")


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


class UserSession(Base):
    __tablename__ = "user_sessions"
    id         = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id    = Column(String, ForeignKey("users.id"), nullable=False)
    token      = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False)
    is_active  = Column(Boolean, default=True)
    user       = relationship("User", back_populates="sessions")


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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    log_system("INFO", "Database initialized.")


# =============================================================
# PYDANTIC SCHEMAS
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

class ChatRequest(BaseModel):
    messages:      List[Dict[str, str]]
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


# =============================================================
# UTILITY FUNCTIONS
# =============================================================

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260000)
    return f"{salt}:{h.hex()}"

def verify_password(password: str, hashed: str) -> bool:
    try:
        salt, h = hashed.split(":")
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
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": "admin" if user.email in ADMIN_EMAILS else user.role,
        "provider": user.provider,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }

def log_system(level: str, message: str):
    db = SessionLocal()
    try:
        db.add(SystemLog(level=level, message=message))
        db.commit()
    except Exception:
        pass
    finally:
        db.close()
    getattr(logger, level.lower(), logger.info)(message)

def log_error(message: str, tb: str = ""):
    db = SessionLocal()
    try:
        db.add(ErrorLog(message=message, traceback=tb))
        db.commit()
    except Exception:
        pass
    finally:
        db.close()
    logger.error(message)

def log_api_usage(provider: str, model: str, tokens: int, latency_ms: int, status: str = "success"):
    db = SessionLocal()
    try:
        db.add(ApiUsageLog(provider=provider, model=model, tokens=tokens, latency_ms=latency_ms, status=status))
        db.commit()
    except Exception:
        pass
    finally:
        db.close()


# =============================================================
# AUTH HELPERS
# =============================================================

def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[User]:
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

def set_auth_cookie(response: Response, token: str, remember: bool = True):
    response.set_cookie(
        key=Config.SESSION_COOKIE,
        value=token,
        httponly=True,
        secure=Config.ENVIRONMENT == "production",
        samesite="lax",
        max_age=60 * 60 * 24 * 30 if remember else None,
    )


# =============================================================
# AI PROVIDER CLIENTS
# =============================================================

PROVIDER_CONFIGS = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "key_env": "OPENAI_API_KEY",
        "key": lambda: Config.OPENAI_API_KEY,
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
        "key": lambda: Config.OPENROUTER_API_KEY,
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "key_env": "GROQ_API_KEY",
        "key": lambda: Config.GROQ_API_KEY,
    },
    "kimi": {
        "base_url": "https://api.moonshot.cn/v1",
        "key_env": "KIMI_API_KEY",
        "key": lambda: Config.KIMI_API_KEY,
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "key_env": "DEEPSEEK_API_KEY",
        "key": lambda: Config.DEEPSEEK_API_KEY,
    },
    "mistral": {
        "base_url": "https://api.mistral.ai/v1",
        "key_env": "MISTRAL_API_KEY",
        "key": lambda: Config.MISTRAL_API_KEY,
    },
    "cohere": {
        "base_url": "https://api.cohere.ai/v1",
        "key_env": "COHERE_API_KEY",
        "key": lambda: Config.COHERE_API_KEY,
    },
    "claude": {
        "base_url": "https://api.anthropic.com/v1",
        "key_env": "CLAUDE_API_KEY",
        "key": lambda: Config.CLAUDE_API_KEY,
    },
}

TOOL_SYSTEM_PROMPTS = {
    "web_search":     "You are a research assistant. Use the provided search results to answer accurately. Always cite your sources.",
    "deep_research":  "You are a deep research expert. Synthesize information from multiple sources into a comprehensive, well-structured report with citations.",
    "translator":     "You are a professional translator. Translate the given text accurately, preserving tone and meaning. Detect the source language automatically.",
    "summarizer":     "You are a summarization expert. Create concise, accurate summaries that capture the key points and main ideas.",
    "rewrite":        "You are a professional editor and writer. Rewrite the given text to improve clarity, flow, and quality while preserving the original meaning.",
    "grammar":        "You are a grammar and style expert. Fix all grammatical errors, spelling mistakes, and improve sentence structure. Show corrections clearly.",
    "explain_code":   "You are a senior software engineer. Explain the given code clearly, describing what it does, how it works, and any important patterns or pitfalls.",
    "code_assistant": "You are an expert software engineer and coding assistant. Write clean, efficient, well-commented code. Follow best practices.",
    "math_solver":    "You are a mathematics expert. Solve problems step-by-step, showing all working. Explain each step clearly.",
    "pdf_chat":       "You are a document analysis expert. Answer questions about the provided document content accurately and comprehensively.",
    "url_reader":     "You are a web content analyst. Analyze the provided URL content and answer questions about it accurately.",
    "image_analysis": "You are a computer vision expert. Analyze the provided image in detail, describing what you see, identifying objects, text, patterns, and providing insights.",
}

DEFAULT_SYSTEM_PROMPT = """You are Bloxy-bot AI, a highly capable and intelligent AI assistant. You are:
- Helpful, accurate, and thorough in your responses
- Capable of coding, analysis, writing, research, math, and more
- Honest about uncertainty — you say when you don't know something
- Concise when appropriate, detailed when needed
- Friendly and professional in tone

Current date: {date}"""


async def call_ai_stream(
    messages: List[Dict],
    model: str,
    provider: str,
    max_tokens: int = 4096,
    temperature: float = 0.7,
    system_prompt: str = "",
    tool: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """Universal streaming AI caller for all providers."""

    cfg = PROVIDER_CONFIGS.get(provider)
    if not cfg:
        raise HTTPException(400, f"Unknown provider: {provider}")

    api_key = cfg["key"]()
    if not api_key:
        raise HTTPException(400, f"API key not configured for provider: {provider}")

    sys_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT.format(date=datetime.now().strftime("%B %d, %Y"))
    if tool and tool in TOOL_SYSTEM_PROMPTS:
        sys_prompt = TOOL_SYSTEM_PROMPTS[tool] + "\n\n" + sys_prompt

    all_messages = [{"role": "system", "content": sys_prompt}] + messages
    start_time = time.time()
    tokens_used = 0

    # ── Anthropic Claude (direct) ─────────────────────────────
    if provider == "claude":
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "stream": True,
            "system": sys_prompt,
            "messages": [m for m in messages if m["role"] != "system"],
        }
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", f"{cfg['base_url']}/messages", headers=headers, json=payload) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    raise HTTPException(resp.status_code, body.decode())
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:].strip()
                        if data == "[DONE]" or not data:
                            continue
                        try:
                            obj = json.loads(data)
                            delta = obj.get("delta", {}).get("text", "")
                            if delta:
                                tokens_used += 1
                                yield f"data: {json.dumps({'choices': [{'delta': {'content': delta}}]})}\n\n"
                        except Exception:
                            pass
        latency = int((time.time() - start_time) * 1000)
        log_api_usage(provider, model, tokens_used, latency)
        return

    # ── Cohere (separate API format) ──────────────────────────
    if provider == "cohere":
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        chat_history = []
        user_message = ""
        for m in messages:
            if m["role"] == "user":
                user_message = m["content"]
            elif m["role"] == "assistant":
                chat_history.append({"role": "CHATBOT", "message": m["content"]})
        payload = {
            "model": model if model.startswith("command") else "command-r-plus",
            "message": user_message,
            "chat_history": chat_history,
            "preamble": sys_prompt,
            "stream": True,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", "https://api.cohere.ai/v1/chat", headers=headers, json=payload) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    raise HTTPException(resp.status_code, body.decode())
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        if obj.get("event_type") == "text-generation":
                            text_chunk = obj.get("text", "")
                            if text_chunk:
                                tokens_used += 1
                                yield f"data: {json.dumps({'choices': [{'delta': {'content': text_chunk}}]})}\n\n"
                    except Exception:
                        pass
        latency = int((time.time() - start_time) * 1000)
        log_api_usage(provider, model, tokens_used, latency)
        return

    # ── OpenAI-compatible (OpenAI, Groq, OpenRouter, Kimi, DeepSeek, Mistral) ──
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if provider == "openrouter":
        headers["HTTP-Referer"] = Config.BASE_URL
        headers["X-Title"] = "Bloxy-bot AI"

    payload = {
        "model": model,
        "messages": all_messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream(
            "POST",
            f"{cfg['base_url']}/chat/completions",
            headers=headers,
            json=payload,
        ) as resp:
            if resp.status_code != 200:
                body = await resp.aread()
                raise HTTPException(resp.status_code, body.decode())
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:].strip()
                    if data == "[DONE]":
                        yield "data: [DONE]\n\n"
                        break
                    if not data:
                        continue
                    try:
                        obj = json.loads(data)
                        delta = obj.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if delta:
                            tokens_used += 1
                            yield f"data: {json.dumps({'choices': [{'delta': {'content': delta}}]})}\n\n"
                        usage = obj.get("usage", {})
                        if usage:
                            tokens_used = usage.get("total_tokens", tokens_used)
                    except Exception:
                        pass

    latency = int((time.time() - start_time) * 1000)
    log_api_usage(provider, model, tokens_used, latency)


async def call_ai_sync(
    messages: List[Dict],
    model: str,
    provider: str,
    max_tokens: int = 2048,
    temperature: float = 0.7,
    system_prompt: str = "",
) -> str:
    """Non-streaming AI call, returns full response string."""
    content = ""
    async for chunk in call_ai_stream(messages, model, provider, max_tokens, temperature, system_prompt):
        if chunk.startswith("data: ") and chunk.strip() != "data: [DONE]":
            try:
                obj = json.loads(chunk[6:].strip())
                content += obj.get("choices", [{}])[0].get("delta", {}).get("content", "")
            except Exception:
                pass
    return content


# =============================================================
# INTEGRATION HELPERS
# =============================================================

async def search_tavily(query: str, max_results: int = 6, search_depth: str = "basic") -> dict:
    if not Config.TAVILY_API_KEY:
        raise HTTPException(400, "Tavily API key not configured.")
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.tavily.com/search",
            json={"api_key": Config.TAVILY_API_KEY, "query": query, "max_results": max_results, "search_depth": search_depth, "include_answer": True},
        )
        resp.raise_for_status()
        return resp.json()

async def search_exa(query: str, num_results: int = 5) -> dict:
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

async def crawl_url_firecrawl(url: str) -> dict:
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

async def search_wikipedia(query: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            "https://en.wikipedia.org/w/api.php",
            params={"action": "query", "list": "search", "srsearch": query, "format": "json", "srlimit": 3, "srprop": "snippet|titlesnippet"},
        )
        resp.raise_for_status()
        return resp.json()

async def get_wikipedia_summary(title: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}")
        resp.raise_for_status()
        return resp.json()

async def search_wikidata(query: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            "https://www.wikidata.org/w/api.php",
            params={"action": "wbsearchentities", "search": query, "language": "en", "format": "json", "limit": 5},
        )
        resp.raise_for_status()
        return resp.json()

async def get_dictionary(word: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.parse.quote(word)}")
        if resp.status_code == 404:
            return {"error": f"No definition found for '{word}'"}
        resp.raise_for_status()
        return resp.json()

async def get_weather(location: str) -> dict:
    if not Config.OPENWEATHER_API_KEY:
        return await get_weather_open_meteo(location)
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": location, "appid": Config.OPENWEATHER_API_KEY, "units": "metric"},
        )
        if resp.status_code == 200:
            return resp.json()
    return await get_weather_open_meteo(location)

async def get_weather_open_meteo(location: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        geo = await client.get("https://geocoding-api.open-meteo.com/v1/search", params={"name": location, "count": 1, "format": "json"})
        geo.raise_for_status()
        geo_data = geo.json()
        if not geo_data.get("results"):
            return {"error": f"Location '{location}' not found."}
        loc = geo_data["results"][0]
        weather = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": loc["latitude"], "longitude": loc["longitude"], "current_weather": True, "hourly": "temperature_2m,precipitation_probability,windspeed_10m", "forecast_days": 1},
        )
        weather.raise_for_status()
        data = weather.json()
        data["location_name"] = loc.get("name", location)
        data["country"] = loc.get("country", "")
        return data

async def get_news(query: str = "", category: str = "general", country: str = "us") -> dict:
    if Config.NEWS_API_KEY:
        async with httpx.AsyncClient(timeout=15) as client:
            params = {"apiKey": Config.NEWS_API_KEY, "language": "en", "pageSize": 8}
            if query:
                params["q"] = query
            else:
                params["category"] = category
                params["country"] = country
            resp = await client.get("https://newsapi.org/v2/top-headlines" if not query else "https://newsapi.org/v2/everything", params=params)
            if resp.status_code == 200:
                return resp.json()
    if Config.GNEWS_API_KEY:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://gnews.io/api/v4/search" if query else "https://gnews.io/api/v4/top-headlines",
                params={"q": query or category, "apikey": Config.GNEWS_API_KEY, "lang": "en", "max": 8},
            )
            if resp.status_code == 200:
                return resp.json()
    # Fallback: Hacker News
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get("https://hacker-news.firebaseio.com/v0/topstories.json")
        ids = resp.json()[:10]
        stories = []
        for sid in ids[:5]:
            s = await client.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
            stories.append(s.json())
        return {"articles": [{"title": s.get("title"), "url": s.get("url"), "source": {"name": "Hacker News"}} for s in stories]}

async def get_stock(symbol: str) -> dict:
    if Config.FINNHUB_API_KEY:
        async with httpx.AsyncClient(timeout=15) as client:
            q = await client.get(f"https://finnhub.io/api/v1/quote", params={"symbol": symbol.upper(), "token": Config.FINNHUB_API_KEY})
            p = await client.get(f"https://finnhub.io/api/v1/stock/profile2", params={"symbol": symbol.upper(), "token": Config.FINNHUB_API_KEY})
            if q.status_code == 200:
                return {"quote": q.json(), "profile": p.json() if p.status_code == 200 else {}}
    if Config.ALPHA_VANTAGE_KEY:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get("https://www.alphavantage.co/query", params={"function": "GLOBAL_QUOTE", "symbol": symbol.upper(), "apikey": Config.ALPHA_VANTAGE_KEY})
            if resp.status_code == 200:
                return resp.json()
    return {"error": "Finance API not configured."}

async def get_crypto(coin: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        params = {"ids": coin.lower(), "vs_currencies": "usd,btc", "include_market_cap": "true", "include_24hr_change": "true"}
        if Config.COINGECKO_API_KEY:
            params["x_cg_demo_api_key"] = Config.COINGECKO_API_KEY
        resp = await client.get("https://api.coingecko.com/api/v3/simple/price", params=params)
        resp.raise_for_status()
        return resp.json()

async def get_exchange_rates(base: str = "USD") -> dict:
    if Config.EXCHANGERATE_KEY:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"https://v6.exchangerate-api.com/v6/{Config.EXCHANGERATE_KEY}/latest/{base}")
            if resp.status_code == 200:
                return resp.json()
    # Free fallback: Frankfurter
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"https://api.frankfurter.app/latest", params={"from": base})
        resp.raise_for_status()
        return resp.json()

async def get_sports_scores(sport: str = "soccer", league: str = "") -> dict:
    if Config.THESPORTSDB_KEY:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"https://www.thesportsdb.com/api/v1/json/{Config.THESPORTSDB_KEY}/eventspastleague.php", params={"id": "4328"})
            if resp.status_code == 200:
                return resp.json()
    if Config.APISPORTS_KEY:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://v3.football.api-sports.io/fixtures",
                headers={"x-apisports-key": Config.APISPORTS_KEY},
                params={"live": "all"},
            )
            if resp.status_code == 200:
                return resp.json()
    return {"error": "Sports API not configured or no live games."}

async def get_tmdb(query: str, media_type: str = "movie") -> dict:
    if not Config.TMDB_API_KEY:
        if Config.OMDB_API_KEY:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get("http://www.omdbapi.com/", params={"apikey": Config.OMDB_API_KEY, "t": query, "type": media_type})
                return resp.json()
        return {"error": "Movie/TV API not configured."}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"https://api.themoviedb.org/3/search/{media_type}",
            params={"api_key": Config.TMDB_API_KEY, "query": query, "language": "en-US"},
        )
        resp.raise_for_status()
        return resp.json()

async def get_country_info(country: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"https://restcountries.com/v3.1/name/{urllib.parse.quote(country)}")
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"Country '{country}' not found."}

async def solve_math_wolfram(query: str) -> dict:
    if not Config.WOLFRAM_APP_ID:
        return {"error": "Wolfram Alpha not configured."}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            "http://api.wolframalpha.com/v2/query",
            params={"input": query, "appid": Config.WOLFRAM_APP_ID, "output": "json", "format": "plaintext"},
        )
        resp.raise_for_status()
        return resp.json()

async def get_open_library(query: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get("https://openlibrary.org/search.json", params={"q": query, "limit": 5, "fields": "title,author_name,first_publish_year,isbn,subject"})
        resp.raise_for_status()
        return resp.json()

async def search_arxiv(query: str, max_results: int = 5) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            "https://export.arxiv.org/api/query",
            params={"search_query": f"all:{query}", "max_results": max_results, "sortBy": "relevance"},
        )
        resp.raise_for_status()
        return {"raw_xml": resp.text[:5000], "query": query}

async def get_duckduckgo_answer(query: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get("https://api.duckduckgo.com/", params={"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"})
        resp.raise_for_status()
        return resp.json()

async def get_ip_info(ip: str = "") -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        url = f"http://ip-api.com/json/{ip}" if ip else "http://ip-api.com/json/"
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()

async def get_food_info(query: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get("https://world.openfoodfacts.org/cgi/search.pl", params={"search_terms": query, "search_simple": 1, "action": "process", "json": 1, "page_size": 5})
        resp.raise_for_status()
        return resp.json()

async def get_tvmaze(query: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get("https://api.tvmaze.com/search/shows", params={"q": query})
        resp.raise_for_status()
        return resp.json()

async def get_pokeapi(pokemon: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon.lower()}")
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"Pokémon '{pokemon}' not found."}

async def send_password_reset_email(email: str, reset_token: str):
    if not Config.RESEND_API_KEY:
        logger.warning(f"Password reset token for {email}: {reset_token}")
        return
    reset_url = f"{Config.BASE_URL}/reset-password?token={reset_token}"
    async with httpx.AsyncClient(timeout=15) as client:
        await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {Config.RESEND_API_KEY}", "Content-Type": "application/json"},
            json={
                "from": "Bloxy-bot AI <noreply@bloxybot.ai>",
                "to": [email],
                "subject": "Reset your Bloxy-bot AI password",
                "html": f"""
                <div style="font-family:Inter,sans-serif;max-width:520px;margin:0 auto;padding:32px;background:#0f0f0f;color:#e5e5e5;border-radius:12px">
                  <h2 style="color:#f97316;margin-bottom:16px">Reset your password</h2>
                  <p style="margin-bottom:20px;color:#a3a3a3">Click the button below to reset your password. This link expires in 24 hours.</p>
                  <a href="{reset_url}" style="display:inline-block;background:#f97316;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600">Reset Password</a>
                  <p style="margin-top:20px;font-size:12px;color:#666">If you didn't request this, ignore this email.</p>
                </div>""",
            },
        )


# =============================================================
# TOOL EXECUTOR
# =============================================================

async def execute_tool(tool: str, user_input: str, messages: List[Dict], model: str, provider: str, options: dict = {}) -> AsyncGenerator[str, None]:
    """Execute a specific tool and stream the result."""

    tool_context = ""

    try:
        if tool == "web_search":
            data = await search_tavily(user_input, max_results=6, search_depth="basic")
            results = data.get("results", [])
            answer = data.get("answer", "")
            tool_context = f"Web search results for: {user_input}\n\n"
            if answer:
                tool_context += f"Quick Answer: {answer}\n\n"
            for r in results:
                tool_context += f"**{r.get('title', '')}**\n{r.get('url', '')}\n{r.get('content', '')[:400]}\n\n"

        elif tool == "deep_research":
            tavily_data = await search_tavily(user_input, max_results=8, search_depth="advanced")
            exa_data = {}
            if Config.EXA_API_KEY:
                try:
                    exa_data = await search_exa(user_input, num_results=5)
                except Exception:
                    pass
            wiki_data = await search_wikipedia(user_input)
            tool_context = f"Deep Research: {user_input}\n\n"
            tool_context += "=== Tavily Sources ===\n"
            for r in tavily_data.get("results", []):
                tool_context += f"• {r.get('title')}: {r.get('content', '')[:500]}\n  Source: {r.get('url', '')}\n\n"
            if exa_data.get("results"):
                tool_context += "=== Exa Sources ===\n"
                for r in exa_data["results"]:
                    tool_context += f"• {r.get('title')}: {r.get('text', '')[:400]}\n  Source: {r.get('url', '')}\n\n"
            wiki_results = wiki_data.get("query", {}).get("search", [])
            if wiki_results:
                tool_context += "=== Wikipedia ===\n"
                for w in wiki_results[:2]:
                    snippet = re.sub(r'<[^>]+>', '', w.get("snippet", ""))
                    tool_context += f"• {w.get('title')}: {snippet}\n\n"

        elif tool == "url_reader":
            url = user_input.strip()
            if not url.startswith("http"):
                url = "https://" + url
            try:
                data = await crawl_url_firecrawl(url)
                content = data.get("data", {}).get("markdown", data.get("data", {}).get("content", ""))
                tool_context = f"Content from {url}:\n\n{content[:4000]}"
            except Exception:
                async with httpx.AsyncClient(timeout=20) as client:
                    resp = await client.get(url, headers={"User-Agent": "Bloxy-bot AI/1.0"})
                    tool_context = f"Content from {url}:\n\n{resp.text[:3000]}"

        elif tool == "translator":
            tool_context = f"Translate the following text (detect language automatically and translate to English unless specified otherwise):\n\n{user_input}"

        elif tool == "summarizer":
            if user_input.startswith("http"):
                try:
                    data = await crawl_url_firecrawl(user_input)
                    content = data.get("data", {}).get("markdown", "")
                    tool_context = f"Summarize this content from {user_input}:\n\n{content[:5000]}"
                except Exception:
                    tool_context = f"Summarize: {user_input}"
            else:
                tool_context = f"Summarize the following text:\n\n{user_input}"

        elif tool == "rewrite":
            style = options.get("style", "professional")
            tool_context = f"Rewrite the following text in a {style} style:\n\n{user_input}"

        elif tool == "grammar":
            tool_context = f"Fix all grammar, spelling, and punctuation errors in the following text. Show the corrected version clearly:\n\n{user_input}"

        elif tool == "explain_code":
            tool_context = f"Explain the following code in detail:\n\n```\n{user_input}\n```"

        elif tool == "code_assistant":
            tool_context = user_input

        elif tool == "math_solver":
            wolfram_result = {}
            if Config.WOLFRAM_APP_ID:
                try:
                    wolfram_result = await solve_math_wolfram(user_input)
                    pods = wolfram_result.get("queryresult", {}).get("pods", [])
                    wolfram_text = "\n".join([f"{p.get('title')}: {p.get('subpods', [{}])[0].get('plaintext', '')}" for p in pods if p.get("subpods")])
                    tool_context = f"Wolfram Alpha result:\n{wolfram_text}\n\nNow solve step by step:\n{user_input}"
                except Exception:
                    tool_context = f"Solve this math problem step by step:\n{user_input}"
            else:
                tool_context = f"Solve this math problem step by step, showing all working:\n{user_input}"

        elif tool == "image_analysis":
            tool_context = user_input

        else:
            tool_context = user_input

    except Exception as e:
        log_error(f"Tool execution error ({tool}): {str(e)}", traceback.format_exc())
        tool_context = f"Note: Tool context retrieval partially failed: {str(e)}\n\nUser query: {user_input}"

    tool_messages = messages.copy()
    if tool_context and tool_context != user_input:
        if tool_messages and tool_messages[-1]["role"] == "user":
            tool_messages[-1] = {"role": "user", "content": f"{tool_context}\n\nUser query: {user_input}"}
        else:
            tool_messages.append({"role": "user", "content": tool_context})

    async for chunk in call_ai_stream(tool_messages, model, provider, tool=tool):
        yield chunk


# =============================================================
# APP FACTORY & LIFESPAN
# =============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    log_system("INFO", "Bloxy-bot AI server started.")
    yield
    log_system("INFO", "Bloxy-bot AI server shutting down.")


app = FastAPI(
    title="Bloxy-bot AI",
    description="Production AI chatbot API",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
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

# Static files & templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# =============================================================
# FRONTEND ROUTE
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
async def register(body: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email.lower()).first():
        raise HTTPException(400, "An account with this email already exists.")
    user = User(
        name=body.name.strip(),
        email=body.email.lower().strip(),
        password=hash_password(body.password),
        provider="email",
        role="admin" if body.email.lower() in ADMIN_EMAILS else "user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_jwt(user.id, user.email)
    set_auth_cookie(response, token)
    log_system("INFO", f"New user registered: {user.email}")
    return {"user": user_to_dict(user)}


@app.post("/api/auth/login")
async def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower().strip()).first()
    if not user or not user.password or not verify_password(body.password, user.password):
        raise HTTPException(401, "Invalid email or password.")
    if not user.is_active:
        raise HTTPException(403, "Account is disabled.")
    token = create_jwt(user.id, user.email)
    set_auth_cookie(response, token, body.remember)
    log_system("INFO", f"User logged in: {user.email}")
    return {"user": user_to_dict(user)}


@app.post("/api/auth/logout")
async def logout(response: Response):
    response.delete_cookie(Config.SESSION_COOKIE)
    return {"message": "Logged out."}


@app.get("/api/auth/me")
async def me(user: Optional[User] = Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated.")
    return {"user": user_to_dict(user)}


@app.post("/api/auth/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower().strip()).first()
    if user:
        reset_token = secrets.token_urlsafe(32)
        background_tasks.add_task(send_password_reset_email, user.email, reset_token)
    return {"message": "If that email is registered, a reset link has been sent."}


# ── Google OAuth ──────────────────────────────────────────────
@app.get("/api/auth/google")
async def google_oauth_redirect():
    if not Config.GOOGLE_CLIENT_ID:
        raise HTTPException(400, "Google OAuth not configured.")
    params = urllib.parse.urlencode({
        "client_id": Config.GOOGLE_CLIENT_ID,
        "redirect_uri": f"{Config.BASE_URL}/api/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
    })
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{params}")


@app.get("/api/auth/google/callback")
async def google_oauth_callback(code: str, response: Response, db: Session = Depends(get_db)):
    if not Config.GOOGLE_CLIENT_ID:
        return RedirectResponse("/?error=oauth_not_configured")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": Config.GOOGLE_CLIENT_ID,
                    "client_secret": Config.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": f"{Config.BASE_URL}/api/auth/google/callback",
                    "grant_type": "authorization_code",
                },
            )
            token_data = token_resp.json()
            user_resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {token_data['access_token']}"},
            )
            user_info = user_resp.json()

        email = user_info.get("email", "").lower()
        name = user_info.get("name", email.split("@")[0])
        provider_id = user_info.get("id", "")

        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(name=name, email=email, provider="google", provider_id=provider_id, role="admin" if email in ADMIN_EMAILS else "user")
            db.add(user)
            db.commit()
            db.refresh(user)

        token = create_jwt(user.id, user.email)
        redirect = RedirectResponse(url="/")
        set_auth_cookie(redirect, token)
        return redirect
    except Exception as e:
        log_error(f"Google OAuth error: {str(e)}", traceback.format_exc())
        return RedirectResponse(f"/?error=google_oauth_failed")


# ── GitHub OAuth ──────────────────────────────────────────────
@app.get("/api/auth/github")
async def github_oauth_redirect():
    if not Config.GITHUB_CLIENT_ID:
        raise HTTPException(400, "GitHub OAuth not configured.")
    params = urllib.parse.urlencode({
        "client_id": Config.GITHUB_CLIENT_ID,
        "redirect_uri": f"{Config.BASE_URL}/api/auth/github/callback",
        "scope": "user:email",
    })
    return RedirectResponse(f"https://github.com/login/oauth/authorize?{params}")


@app.get("/api/auth/github/callback")
async def github_oauth_callback(code: str, response: Response, db: Session = Depends(get_db)):
    if not Config.GITHUB_CLIENT_ID:
        return RedirectResponse("/?error=oauth_not_configured")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            token_resp = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={"client_id": Config.GITHUB_CLIENT_ID, "client_secret": Config.GITHUB_CLIENT_SECRET, "code": code},
            )
            token_data = token_resp.json()
            access_token = token_data.get("access_token", "")
            user_resp = await client.get("https://api.github.com/user", headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"})
            user_info = user_resp.json()
            emails_resp = await client.get("https://api.github.com/user/emails", headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"})
            emails = emails_resp.json()

        primary_email = next((e["email"] for e in emails if e.get("primary") and e.get("verified")), None)
        if not primary_email:
            primary_email = user_info.get("email") or f"{user_info.get('login', 'user')}@github.local"
        primary_email = primary_email.lower()
        name = user_info.get("name") or user_info.get("login", "GitHub User")
        provider_id = str(user_info.get("id", ""))

        user = db.query(User).filter(User.email == primary_email).first()
        if not user:
            user = User(name=name, email=primary_email, provider="github", provider_id=provider_id, role="admin" if primary_email in ADMIN_EMAILS else "user")
            db.add(user)
            db.commit()
            db.refresh(user)

        token = create_jwt(user.id, user.email)
        redirect = RedirectResponse(url="/")
        set_auth_cookie(redirect, token)
        return redirect
    except Exception as e:
        log_error(f"GitHub OAuth error: {str(e)}", traceback.format_exc())
        return RedirectResponse("/?error=github_oauth_failed")


# =============================================================
# CHAT ROUTES
# =============================================================

@app.post("/api/chat")
async def chat(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    content_type = request.headers.get("content-type", "")
    file_content: Optional[str] = None
    file_name: Optional[str] = None

    if "multipart/form-data" in content_type:
        form = await request.form()
        data = json.loads(form.get("data", "{}"))
        file = form.get("file")
        if file and hasattr(file, "read"):
            file_bytes = await file.read()
            file_name = file.filename
            mime = file.content_type or ""
            if "pdf" in mime:
                try:
                    import pdfplumber
                    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                        file_content = "\n".join(page.extract_text() or "" for page in pdf.pages[:20])
                except ImportError:
                    try:
                        from pypdf import PdfReader
                        reader = PdfReader(io.BytesIO(file_bytes))
                        file_content = "\n".join(page.extract_text() or "" for page in reader.pages[:20])
                    except Exception:
                        file_content = "[PDF content could not be extracted]"
            elif "image" in mime:
                import base64
                file_content = f"[IMAGE:{base64.b64encode(file_bytes).decode()}:{mime}]"
            else:
                file_content = file_bytes.decode("utf-8", errors="replace")[:5000]
    else:
        body_bytes = await request.body()
        data = json.loads(body_bytes)

    body = ChatRequest(**data)

    messages = body.messages.copy()
    if file_content and messages:
        if "[IMAGE:" in file_content:
            b64, mime = file_content[7:].rsplit(":", 1)
            messages[-1]["content"] = [
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                {"type": "text", "text": messages[-1].get("content", "")},
            ]
        else:
            messages[-1]["content"] = f"File: {file_name}\n\n{file_content}\n\nUser query: {messages[-1].get('content', '')}"

    # Save chat to DB
    chat_id = body.chat_id
    if current_user and messages:
        try:
            if not chat_id:
                title = messages[-1].get("content", "New Chat")
                if isinstance(title, list):
                    title = "Image Analysis"
                chat_obj = Chat(user_id=current_user.id, title=title[:80], model=body.model, provider=body.provider)
                db.add(chat_obj)
                db.commit()
                chat_id = chat_obj.id
            for msg in messages[-2:]:
                db.add(Message(chat_id=chat_id, role=msg.get("role", "user"), content=str(msg.get("content", ""))[:10000], model=body.model))
            db.commit()
        except Exception as e:
            log_error(f"Chat DB save error: {str(e)}")

    async def stream_generator():
        try:
            if body.tool:
                user_input = messages[-1].get("content", "") if messages else ""
                if isinstance(user_input, list):
                    user_input = next((c.get("text", "") for c in user_input if isinstance(c, dict) and c.get("type") == "text"), "")
                async for chunk in execute_tool(body.tool, user_input, messages[:-1], body.model, body.provider, body.options if hasattr(body, "options") else {}):
                    yield chunk
            elif body.web_search and messages:
                user_input = messages[-1].get("content", "")
                if isinstance(user_input, list):
                    user_input = next((c.get("text", "") for c in user_input if isinstance(c, dict) and c.get("type") == "text"), "")
                async for chunk in execute_tool("web_search", user_input, messages[:-1], body.model, body.provider):
                    yield chunk
            else:
                async for chunk in call_ai_stream(messages, body.model, body.provider, body.max_tokens, body.temperature, body.system_prompt or ""):
                    yield chunk
        except HTTPException as e:
            yield f"data: {json.dumps({'error': e.detail})}\n\n"
        except Exception as e:
            log_error(f"Stream error: {str(e)}", traceback.format_exc())
            yield f"data: {json.dumps({'error': 'Internal server error. Please try again.'})}\n\n"

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# =============================================================
# TOOL ROUTES
# =============================================================

@app.get("/api/tools/weather")
async def weather_route(location: str):
    try:
        data = await get_weather(location)
        return data
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/tools/news")
async def news_route(q: str = "", category: str = "general"):
    try:
        return await get_news(q, category)
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/tools/stock")
async def stock_route(symbol: str):
    try:
        return await get_stock(symbol)
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/tools/crypto")
async def crypto_route(coin: str):
    try:
        return await get_crypto(coin)
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/tools/exchange")
async def exchange_route(base: str = "USD"):
    try:
        return await get_exchange_rates(base)
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/tools/sports")
async def sports_route(sport: str = "soccer", league: str = ""):
    try:
        return await get_sports_scores(sport, league)
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/tools/movies")
async def movies_route(q: str, type: str = "movie"):
    try:
        return await get_tmdb(q, type)
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/tools/wikipedia")
async def wikipedia_route(q: str):
    try:
        return await get_wikipedia_summary(q)
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/tools/dictionary")
async def dictionary_route(word: str):
    try:
        return await get_dictionary(word)
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/tools/books")
async def books_route(q: str):
    try:
        return await get_open_library(q)
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/tools/arxiv")
async def arxiv_route(q: str):
    try:
        return await search_arxiv(q)
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/tools/country")
async def country_route(name: str):
    try:
        return await get_country_info(name)
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/tools/food")
async def food_route(q: str):
    try:
        return await get_food_info(q)
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/tools/pokemon")
async def pokemon_route(name: str):
    try:
        return await get_pokeapi(name)
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/tools/tvshows")
async def tvshows_route(q: str):
    try:
        return await get_tvmaze(q)
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/tools/duckduckgo")
async def ddg_route(q: str):
    try:
        return await get_duckduckgo_answer(q)
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/tools/ip")
async def ip_route(ip: str = ""):
    try:
        return await get_ip_info(ip)
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/tools/search")
async def search_route(body: ToolRequest):
    try:
        if Config.TAVILY_API_KEY:
            return await search_tavily(body.input)
        return await get_duckduckgo_answer(body.input)
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/tools/deep-research")
async def deep_research_route(body: ToolRequest, current_user: Optional[User] = Depends(get_current_user)):
    try:
        results = {}
        if Config.TAVILY_API_KEY:
            results["tavily"] = await search_tavily(body.input, max_results=8, search_depth="advanced")
        if Config.EXA_API_KEY:
            results["exa"] = await search_exa(body.input, num_results=6)
        results["wikipedia"] = await search_wikipedia(body.input)
        return results
    except Exception as e:
        raise HTTPException(500, str(e))


# =============================================================
# ADMIN ROUTES
# =============================================================

@app.get("/api/admin/stats")
async def admin_stats(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        total_users     = db.query(func.count(User.id)).scalar() or 0
        total_chats     = db.query(func.count(Chat.id)).scalar() or 0
        messages_today  = db.query(func.count(Message.id)).filter(Message.created_at >= today).scalar() or 0
        api_calls_today = db.query(func.count(ApiUsageLog.id)).filter(ApiUsageLog.created_at >= today).scalar() or 0
        errors_24h      = db.query(func.count(ErrorLog.id)).filter(ErrorLog.created_at >= datetime.now(timezone.utc) - timedelta(hours=24)).scalar() or 0
        active_sessions = db.query(func.count(UserSession.id)).filter(UserSession.is_active == True, UserSession.expires_at > datetime.now(timezone.utc)).scalar() or 0
        return {
            "total_users": total_users,
            "total_chats": total_chats,
            "messages_today": messages_today,
            "api_calls_today": api_calls_today,
            "errors_24h": errors_24h,
            "active_sessions": active_sessions,
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/admin/users")
async def admin_users(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).limit(100).all()
    return {
        "users": [
            {**user_to_dict(u), "chat_count": db.query(func.count(Chat.id)).filter(Chat.user_id == u.id).scalar() or 0}
            for u in users
        ]
    }


@app.get("/api/admin/chat-logs")
async def admin_chat_logs(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    chats = db.query(Chat).order_by(Chat.created_at.desc()).limit(100).all()
    return {
        "logs": [
            {
                "id": c.id,
                "user_email": db.query(User.email).filter(User.id == c.user_id).scalar() or "Guest",
                "model": c.model,
                "message_count": c.message_count,
                "total_tokens": c.total_tokens,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in chats
        ]
    }


@app.get("/api/admin/api-usage")
async def admin_api_usage(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    logs = db.query(ApiUsageLog).filter(ApiUsageLog.created_at >= today).all()
    by_provider: Dict[str, dict] = {}
    for log in logs:
        p = log.provider
        if p not in by_provider:
            by_provider[p] = {"requests": 0, "tokens": 0, "latencies": []}
        by_provider[p]["requests"] += 1
        by_provider[p]["tokens"] += log.tokens or 0
        if log.latency_ms:
            by_provider[p]["latencies"].append(log.latency_ms)
    result = {}
    for p, d in by_provider.items():
        avg_lat = int(sum(d["latencies"]) / len(d["latencies"])) if d["latencies"] else 0
        result[p] = {"requests": d["requests"], "tokens": d["tokens"], "avg_latency": avg_lat}
    return result


@app.get("/api/admin/provider-status")
async def admin_provider_status(admin: User = Depends(require_admin)):
    providers = {
        "openai":      ("https://api.openai.com/v1/models",                  {"Authorization": f"Bearer {Config.OPENAI_API_KEY}"}),
        "groq":        ("https://api.groq.com/openai/v1/models",             {"Authorization": f"Bearer {Config.GROQ_API_KEY}"}),
        "openrouter":  ("https://openrouter.ai/api/v1/models",               {"Authorization": f"Bearer {Config.OPENROUTER_API_KEY}"}),
        "kimi":        ("https://api.moonshot.cn/v1/models",                 {"Authorization": f"Bearer {Config.KIMI_API_KEY}"}),
        "deepseek":    ("https://api.deepseek.com/v1/models",                {"Authorization": f"Bearer {Config.DEEPSEEK_API_KEY}"}),
        "mistral":     ("https://api.mistral.ai/v1/models",                  {"Authorization": f"Bearer {Config.MISTRAL_API_KEY}"}),
        "claude":      ("https://api.anthropic.com/v1/models",               {"x-api-key": Config.CLAUDE_API_KEY, "anthropic-version": "2023-06-01"}),
        "tavily":      ("https://api.tavily.com/search",                     {}),
        "exa":         ("https://api.exa.ai/search",                         {}),
        "firecrawl":   ("https://api.firecrawl.dev/v0/scrape",               {}),
        "weather":     (f"https://api.openweathermap.org/data/2.5/weather?q=London&appid={Config.OPENWEATHER_API_KEY}", {}),
        "news":        (f"https://newsapi.org/v2/top-headlines?country=us&apiKey={Config.NEWS_API_KEY}&pageSize=1", {}),
        "finnhub":     (f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={Config.FINNHUB_API_KEY}", {}),
        "sports":      ("https://www.thesportsdb.com/api/v1/json/1/search_all_leagues.php?s=Soccer", {}),
        "tmdb":        (f"https://api.themoviedb.org/3/configuration?api_key={Config.TMDB_API_KEY}", {}),
    }
    results = {}
    async with httpx.AsyncClient(timeout=8) as client:
        for name, (url, headers) in providers.items():
            if not url or ("apiKey=" in url and url.endswith("=")) or ("token=" in url and url.endswith("=")):
                results[name] = {"status": "not_configured", "latency": None}
                continue
            try:
                start = time.time()
                r = await client.get(url, headers=headers)
                latency = int((time.time() - start) * 1000)
                results[name] = {"status": "online" if r.status_code < 500 else "offline", "latency": latency}
            except Exception:
                results[name] = {"status": "offline", "latency": None}
    return results


@app.get("/api/admin/system-logs")
async def admin_system_logs(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    logs = db.query(SystemLog).order_by(SystemLog.created_at.desc()).limit(200).all()
    return {"logs": [{"level": l.level, "message": l.message, "timestamp": l.created_at.isoformat()} for l in logs]}


@app.get("/api/admin/error-logs")
async def admin_error_logs(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    logs = db.query(ErrorLog).order_by(ErrorLog.created_at.desc()).limit(200).all()
    return {"logs": [{"message": l.message, "traceback": l.traceback, "timestamp": l.created_at.isoformat()} for l in logs]}


# =============================================================
# HEALTH CHECK
# =============================================================

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "app": "Bloxy-bot AI",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": Config.ENVIRONMENT,
    }


# =============================================================
# ERROR HANDLERS
# =============================================================

@app.exception_handler(404)
async def not_found(request: Request, exc):
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": "Endpoint not found."}, status_code=404)
 return templates.TemplateResponse(request=request, name="index.html", status_code=200)
 
@app.exception_handler(500)
async def server_error(request: Request, exc):
    log_error(f"500 error on {request.url.path}: {str(exc)}", traceback.format_exc())
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
    )
