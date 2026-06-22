# ============================================================
# SCRIPT 1
# PART 1A — CORE PLATFORM FOUNDATION
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
import os
import uuid
import time
import logging

# ============================================================
# 1A.1 APPLICATION CONFIGURATION
# ============================================================

class Settings(BaseModel):
    app_name: str = "AI Platform"
    version: str = "1.0.0"
    environment: str = os.getenv(
        "ENVIRONMENT",
        "development"
    )

    debug: bool = (
        os.getenv("DEBUG", "false")
        .lower() == "true"
    )

settings = Settings()

# ============================================================
# 1A.2 SERVICE REGISTRY
# ============================================================

class ServiceRegistry:
    def __init__(self):
        self._services = {}

    def register(
        self,
        name: str,
        service: Any
    ):
        self._services[name] = service

    def get(
        self,
        name: str
    ):
        return self._services.get(name)

    def all(self):
        return self._services


services = ServiceRegistry()

# ============================================================
# 1A.3 EVENT BUS
# ============================================================

class EventBus:
    def __init__(self):
        self.events = []

    def emit(
        self,
        event_type: str,
        payload: dict
    ):
        self.events.append(
            {
                "event": event_type,
                "payload": payload,
                "timestamp": int(time.time())
            }
        )

event_bus = EventBus()

# ============================================================
# 1A.4 HEALTH MANAGER
# ============================================================

class HealthManager:
    def __init__(self):
        self.status = "healthy"

    def get_status(self):
        return self.status

health_manager = HealthManager()

# ============================================================
# 1A.5 REQUEST CONTEXT
# ============================================================

class RequestContext(BaseModel):
    request_id: str
    timestamp: int
    workspace_id: Optional[str] = None
    user_id: Optional[str] = None

# ============================================================
# 1A.6 ERROR MODELS
# ============================================================

class PlatformError(Exception):
    def __init__(
        self,
        code: str,
        message: str
    ):
        self.code = code
        self.message = message

class ValidationError(
    PlatformError
):
    pass

class AuthenticationError(
    PlatformError
):
    pass

class AuthorizationError(
    PlatformError
):
    pass

# ============================================================
# 1A.7 LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s "
        "%(levelname)s "
        "%(message)s"
    )
)

logger = logging.getLogger(
    "ai-platform"
)

# ============================================================
# 1A.8 LIFECYCLE MANAGEMENT
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info(
        "Starting AI Platform"
    )

    services.register(
        "event_bus",
        event_bus
    )

    services.register(
        "health",
        health_manager
    )

    event_bus.emit(
        "application_started",
        {
            "version":
            settings.version
        }
    )

    yield

    event_bus.emit(
        "application_shutdown",
        {}
    )

    logger.info(
        "Shutting down AI Platform"
    )

# ============================================================
# 1A.9 APPLICATION INSTANCE
# ============================================================

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    lifespan=lifespan
)

# ============================================================
# 1A.10 REQUEST MIDDLEWARE
# ============================================================

@app.middleware("http")
async def request_middleware(
    request: Request,
    call_next
):
    request_id = str(
        uuid.uuid4()
    )

    request.state.request_id = (
        request_id
    )

    start = time.time()

    response = await call_next(
        request
    )

    duration = (
        time.time() - start
    )

    logger.info(
        f"{request.method} "
        f"{request.url.path} "
        f"{duration:.3f}s"
    )

    response.headers[
        "X-Request-ID"
    ] = request_id

    return response

# ============================================================
# 1A.11 GLOBAL ERROR HANDLER
# ============================================================

@app.exception_handler(
    PlatformError
)
async def platform_error_handler(
    request: Request,
    exc: PlatformError
):
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": exc.code,
            "message": exc.message
        }
    )

# ============================================================
# 1A.12 HEALTH ENDPOINT
# ============================================================

@app.get("/health")
async def health():

    return {
        "status":
            health_manager
            .get_status(),
        "version":
            settings.version,
        "environment":
            settings.environment
    }

# ============================================================
# 1A.13 VERSION ENDPOINT
# ============================================================

@app.get("/version")
async def version():

    return {
        "app":
            settings.app_name,
        "version":
            settings.version
    }

# ============================================================
# 1A.14 ROOT ENDPOINT
# ============================================================

@app.get("/")
async def root():

    return {
        "name":
            settings.app_name,
        "version":
            settings.version,
        "status":
            "running"
    }

# ============================================================
# 1A.15 SERVICE INSPECTION
# ============================================================

@app.get("/system/services")
async def system_services():

    return {
        "services":
            list(
                services
                .all()
                .keys()
            )
    }

# ============================================================
# PART 1A DELIVERABLE
# ============================================================
#
#  FastAPI application
#  Configuration system
#  Service registry
#  Event bus
#  Health manager
#  Request lifecycle
#  Logging framework
#  Error framework
#  Startup/shutdown lifecycle
#  Version management
#  Middleware foundation
#  Platform bootstrap
#
# Ready for PART 1B — AI Gateway
# ============================================================
# ============================================================
# SCRIPT 1
# PART 1B — AI GATEWAY
# Paste directly below Part 1A
# ============================================================

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import time

# ============================================================
# 1B.1 REQUEST MODELS
# ============================================================

class ChatMessage(BaseModel):
    role: str
    content: str


class InferenceRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = 4096
    stream: bool = False


class InferenceResponse(BaseModel):
    provider: str
    model: str
    content: str
    usage: Dict[str, Any]
    latency_ms: int


# ============================================================
# 1B.2 PROVIDER ABSTRACTION
# ============================================================

class BaseProvider:

    provider_name = "base"

    async def chat(
        self,
        request: InferenceRequest
    ):
        raise NotImplementedError


# ============================================================
# 1B.3 PROVIDER REGISTRY
# ============================================================

class ProviderRegistry:

    def __init__(self):
        self.providers = {}

    def register(
        self,
        provider_id: str,
        provider: BaseProvider
    ):
        self.providers[
            provider_id
        ] = provider

    def get(
        self,
        provider_id: str
    ):
        return self.providers.get(
            provider_id
        )

    def all(self):
        return self.providers


provider_registry = ProviderRegistry()

# ============================================================
# 1B.4 OPENAI ADAPTER PLACEHOLDER
# ============================================================

class OpenAIProvider(
    BaseProvider
):

    provider_name = "openai"

    async def chat(
        self,
        request: InferenceRequest
    ):

        return InferenceResponse(
            provider="openai",
            model=request.model,
            content="OpenAI response placeholder",
            usage={
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            },
            latency_ms=0
        )


# ============================================================
# 1B.5 ANTHROPIC ADAPTER PLACEHOLDER
# ============================================================

class AnthropicProvider(
    BaseProvider
):

    provider_name = "anthropic"

    async def chat(
        self,
        request: InferenceRequest
    ):

        return InferenceResponse(
            provider="anthropic",
            model=request.model,
            content="Anthropic response placeholder",
            usage={
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            },
            latency_ms=0
        )


# ============================================================
# 1B.6 GEMINI ADAPTER PLACEHOLDER
# ============================================================

class GeminiProvider(
    BaseProvider
):

    provider_name = "google"

    async def chat(
        self,
        request: InferenceRequest
    ):

        return InferenceResponse(
            provider="google",
            model=request.model,
            content="Gemini response placeholder",
            usage={
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            },
            latency_ms=0
        )


# ============================================================
# 1B.7 PROVIDER REGISTRATION
# ============================================================

provider_registry.register(
    "openai",
    OpenAIProvider()
)

provider_registry.register(
    "anthropic",
    AnthropicProvider()
)

provider_registry.register(
    "google",
    GeminiProvider()
)

# ============================================================
# 1B.8 MODEL ROUTING
# ============================================================

MODEL_ROUTING = {
    "gpt": "openai",
    "claude": "anthropic",
    "gemini": "google"
}


def route_provider(
    model: str
):

    model_lower = model.lower()

    for key, provider in (
        MODEL_ROUTING.items()
    ):
        if key in model_lower:
            return provider

    return "openai"


# ============================================================
# 1B.9 CAPABILITY REGISTRY
# ============================================================

MODEL_CAPABILITIES = {
    "chat": True,
    "streaming": True,
    "vision": True,
    "reasoning": True,
    "tools": True
}

# ============================================================
# 1B.10 REQUEST VALIDATION
# ============================================================

def validate_request(
    request: InferenceRequest
):

    if not request.messages:
        raise ValidationError(
            "EMPTY_MESSAGES",
            "Messages required"
        )

    if not request.model:
        raise ValidationError(
            "MODEL_REQUIRED",
            "Model required"
        )

# ============================================================
# 1B.11 RESPONSE NORMALIZATION
# ============================================================

def normalize_response(
    response: InferenceResponse
):

    return {
        "provider":
            response.provider,
        "model":
            response.model,
        "content":
            response.content,
        "usage":
            response.usage,
        "latency_ms":
            response.latency_ms
    }

# ============================================================
# 1B.12 GATEWAY EXECUTION
# ============================================================

async def execute_inference(
    request: InferenceRequest
):

    validate_request(
        request
    )

    provider_id = (
        route_provider(
            request.model
        )
    )

    provider = (
        provider_registry.get(
            provider_id
        )
    )

    if not provider:
        raise ValidationError(
            "PROVIDER_NOT_FOUND",
            provider_id
        )

    start = time.time()

    result = await provider.chat(
        request
    )

    latency = int(
        (
            time.time()
            - start
        )
        * 1000
    )

    result.latency_ms = (
        latency
    )

    return normalize_response(
        result
    )

# ============================================================
# 1B.13 INFERENCE ENDPOINT
# ============================================================

@app.post("/v1/chat")
async def chat_endpoint(
    request: InferenceRequest
):

    return await execute_inference(
        request
    )

# ============================================================
# 1B.14 PROVIDER LIST ENDPOINT
# ============================================================

@app.get("/v1/providers")
async def get_providers():

    return {
        "providers":
            list(
                provider_registry
                .all()
                .keys()
            )
    }

# ============================================================
# 1B.15 MODEL CAPABILITIES ENDPOINT
# ============================================================

@app.get("/v1/capabilities")
async def capabilities():

    return MODEL_CAPABILITIES

# ============================================================
# PART 1B DELIVERABLE
#
# Unified AI Gateway
# Provider Registry
# OpenAI Adapter Placeholder
# Anthropic Adapter Placeholder
# Gemini Adapter Placeholder
# Model Routing
# Request Validation
# Response Normalization
# Inference Execution
# Provider Discovery Endpoint
# Capabilities Endpoint
#
# Ready For Part 1C
# ============================================================
# ============================================================
# SCRIPT 1
# PART 1C — AUTHENTICATION & USER MANAGEMENT
# Paste directly below Part 1B
# ============================================================

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
import secrets
import hashlib

# ============================================================
# 1C.1 USER MODEL
# ============================================================

class User(BaseModel):
    id: str
    email: EmailStr
    username: str
    password_hash: str
    active: bool = True
    created_at: datetime

# ============================================================
# 1C.2 SESSION MODEL
# ============================================================

class Session(BaseModel):
    token: str
    user_id: str
    created_at: datetime
    expires_at: datetime

# ============================================================
# 1C.3 ROLE MODEL
# ============================================================

class UserRole(BaseModel):
    user_id: str
    role: str

# ============================================================
# 1C.4 IN-MEMORY STORAGE
# ============================================================

USERS = {}
SESSIONS = {}
USER_ROLES = {}

# ============================================================
# 1C.5 PASSWORD HASHING
# ============================================================

def hash_password(
    password: str
) -> str:

    return hashlib.sha256(
        password.encode()
    ).hexdigest()

# ============================================================
# 1C.6 PASSWORD VERIFICATION
# ============================================================

def verify_password(
    password: str,
    password_hash: str
) -> bool:

    return (
        hash_password(password)
        == password_hash
    )

# ============================================================
# 1C.7 TOKEN GENERATION
# ============================================================

def generate_token():

    return secrets.token_urlsafe(
        64
    )

# ============================================================
# 1C.8 REGISTER REQUEST
# ============================================================

class RegisterRequest(
    BaseModel
):
    email: EmailStr
    username: str
    password: str

# ============================================================
# 1C.9 LOGIN REQUEST
# ============================================================

class LoginRequest(
    BaseModel
):
    email: EmailStr
    password: str

# ============================================================
# 1C.10 USER CREATION
# ============================================================

def create_user(
    email: str,
    username: str,
    password: str
):

    user_id = generate_token()

    user = User(
        id=user_id,
        email=email,
        username=username,
        password_hash=
            hash_password(password),
        created_at=
            datetime.utcnow()
    )

    USERS[user_id] = user

    USER_ROLES[user_id] = "member"

    return user

# ============================================================
# 1C.11 USER LOOKUP
# ============================================================

def get_user_by_email(
    email: str
):

    for user in USERS.values():

        if user.email == email:
            return user

    return None

# ============================================================
# 1C.12 SESSION CREATION
# ============================================================

def create_session(
    user_id: str
):

    token = generate_token()

    session = Session(
        token=token,
        user_id=user_id,
        created_at=
            datetime.utcnow(),
        expires_at=
            datetime.utcnow()
            + timedelta(days=30)
    )

    SESSIONS[token] = session

    return session

# ============================================================
# 1C.13 SESSION VALIDATION
# ============================================================

def validate_session(
    token: str
):

    session = SESSIONS.get(
        token
    )

    if not session:
        return None

    if (
        session.expires_at
        < datetime.utcnow()
    ):
        return None

    return session

# ============================================================
# 1C.14 CURRENT USER
# ============================================================

def get_current_user(
    token: str
):

    session = validate_session(
        token
    )

    if not session:
        return None

    return USERS.get(
        session.user_id
    )

# ============================================================
# 1C.15 ROLE CHECK
# ============================================================

def has_role(
    user_id: str,
    role: str
):

    return (
        USER_ROLES.get(user_id)
        == role
    )

# ============================================================
# 1C.16 REGISTER ENDPOINT
# ============================================================

@app.post("/auth/register")
async def register(
    request:
    RegisterRequest
):

    existing = (
        get_user_by_email(
            request.email
        )
    )

    if existing:
        raise ValidationError(
            "EMAIL_EXISTS",
            "Email already exists"
        )

    user = create_user(
        request.email,
        request.username,
        request.password
    )

    return {
        "user_id": user.id,
        "email": user.email,
        "username":
            user.username
    }

# ============================================================
# 1C.17 LOGIN ENDPOINT
# ============================================================

@app.post("/auth/login")
async def login(
    request:
    LoginRequest
):

    user = get_user_by_email(
        request.email
    )

    if not user:
        raise AuthenticationError(
            "INVALID_LOGIN",
            "Invalid credentials"
        )

    if not verify_password(
        request.password,
        user.password_hash
    ):
        raise AuthenticationError(
            "INVALID_LOGIN",
            "Invalid credentials"
        )

    session = create_session(
        user.id
    )

    return {
        "token":
            session.token,
        "expires_at":
            session.expires_at
    }

# ============================================================
# 1C.18 PROFILE ENDPOINT
# ============================================================

@app.get("/auth/profile")
async def profile(
    token: str
):

    user = get_current_user(
        token
    )

    if not user:
        raise AuthenticationError(
            "UNAUTHORIZED",
            "Login required"
        )

    return {
        "id": user.id,
        "email": user.email,
        "username":
            user.username
    }

# ============================================================
# 1C.19 LOGOUT ENDPOINT
# ============================================================

@app.post("/auth/logout")
async def logout(
    token: str
):

    if token in SESSIONS:
        del SESSIONS[token]

    return {
        "success": True
    }

# ============================================================
# 1C.20 ROLE ENDPOINT
# ============================================================

@app.get("/auth/role")
async def role(
    token: str
):

    user = get_current_user(
        token
    )

    if not user:
        raise AuthenticationError(
            "UNAUTHORIZED",
            "Login required"
        )

    return {
        "role":
            USER_ROLES.get(
                user.id
            )
    }

# ============================================================
# PART 1C DELIVERABLE
#
# User Model
# Session Model
# Role Model
# Password Hashing
# Password Verification
# Session Management
# Token Generation
# User Registration
# User Login
# User Logout
# Profile Endpoint
# Role Endpoint
#
# Ready For Part 1D
# ============================================================
# ============================================================
# SCRIPT 1
# PART 1D — WORKSPACE MANAGEMENT
# Paste directly below Part 1C
# ============================================================

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

# ============================================================
# 1D.1 WORKSPACE MODEL
# ============================================================

class Workspace(BaseModel):
    id: str
    name: str
    owner_id: str
    created_at: datetime
    active: bool = True

# ============================================================
# 1D.2 WORKSPACE MEMBER MODEL
# ============================================================

class WorkspaceMember(BaseModel):
    workspace_id: str
    user_id: str
    role: str
    joined_at: datetime

# ============================================================
# 1D.3 WORKSPACE SETTINGS MODEL
# ============================================================

class WorkspaceSettings(BaseModel):
    workspace_id: str
    default_model: str = "gpt-5"
    allow_streaming: bool = True
    allow_tools: bool = True

# ============================================================
# 1D.4 STORAGE
# ============================================================

WORKSPACES = {}
WORKSPACE_MEMBERS = {}
WORKSPACE_SETTINGS = {}

# ============================================================
# 1D.5 CREATE WORKSPACE REQUEST
# ============================================================

class CreateWorkspaceRequest(
    BaseModel
):
    name: str
    owner_id: str

# ============================================================
# 1D.6 UPDATE WORKSPACE REQUEST
# ============================================================

class UpdateWorkspaceRequest(
    BaseModel
):
    name: Optional[str] = None
    active: Optional[bool] = None

# ============================================================
# 1D.7 CREATE WORKSPACE
# ============================================================

def create_workspace(
    name: str,
    owner_id: str
):

    workspace_id = str(
        uuid.uuid4()
    )

    workspace = Workspace(
        id=workspace_id,
        name=name,
        owner_id=owner_id,
        created_at=
            datetime.utcnow()
    )

    WORKSPACES[
        workspace_id
    ] = workspace

    WORKSPACE_MEMBERS[
        workspace_id
    ] = []

    WORKSPACE_MEMBERS[
        workspace_id
    ].append(
        WorkspaceMember(
            workspace_id=
                workspace_id,
            user_id=owner_id,
            role="owner",
            joined_at=
                datetime.utcnow()
        )
    )

    WORKSPACE_SETTINGS[
        workspace_id
    ] = WorkspaceSettings(
        workspace_id=
            workspace_id
    )

    return workspace

# ============================================================
# 1D.8 GET WORKSPACE
# ============================================================

def get_workspace(
    workspace_id: str
):

    return WORKSPACES.get(
        workspace_id
    )

# ============================================================
# 1D.9 ADD MEMBER
# ============================================================

def add_member(
    workspace_id: str,
    user_id: str,
    role: str = "member"
):

    member = WorkspaceMember(
        workspace_id=
            workspace_id,
        user_id=user_id,
        role=role,
        joined_at=
            datetime.utcnow()
    )

    WORKSPACE_MEMBERS[
        workspace_id
    ].append(member)

    return member

# ============================================================
# 1D.10 REMOVE MEMBER
# ============================================================

def remove_member(
    workspace_id: str,
    user_id: str
):

    members = (
        WORKSPACE_MEMBERS.get(
            workspace_id,
            []
        )
    )

    WORKSPACE_MEMBERS[
        workspace_id
    ] = [
        m
        for m in members
        if m.user_id != user_id
    ]

# ============================================================
# 1D.11 LIST MEMBERS
# ============================================================

def list_members(
    workspace_id: str
):

    return (
        WORKSPACE_MEMBERS.get(
            workspace_id,
            []
        )
    )

# ============================================================
# 1D.12 UPDATE SETTINGS
# ============================================================

def update_workspace_settings(
    workspace_id: str,
    settings:
    WorkspaceSettings
):

    WORKSPACE_SETTINGS[
        workspace_id
    ] = settings

# ============================================================
# 1D.13 CREATE WORKSPACE ENDPOINT
# ============================================================

@app.post("/workspaces")
async def create_workspace_api(
    request:
    CreateWorkspaceRequest
):

    workspace = (
        create_workspace(
            request.name,
            request.owner_id
        )
    )

    return workspace

# ============================================================
# 1D.14 GET WORKSPACE ENDPOINT
# ============================================================

@app.get(
    "/workspaces/{workspace_id}"
)
async def get_workspace_api(
    workspace_id: str
):

    workspace = (
        get_workspace(
            workspace_id
        )
    )

    if not workspace:
        raise ValidationError(
            "WORKSPACE_NOT_FOUND",
            "Workspace not found"
        )

    return workspace

# ============================================================
# 1D.15 LIST WORKSPACES ENDPOINT
# ============================================================

@app.get("/workspaces")
async def list_workspaces():

    return {
        "workspaces":
            list(
                WORKSPACES.values()
            )
    }

# ============================================================
# 1D.16 ADD MEMBER ENDPOINT
# ============================================================

@app.post(
    "/workspaces/{workspace_id}/members"
)
async def add_member_api(
    workspace_id: str,
    user_id: str,
    role: str = "member"
):

    return add_member(
        workspace_id,
        user_id,
        role
    )

# ============================================================
# 1D.17 REMOVE MEMBER ENDPOINT
# ============================================================

@app.delete(
    "/workspaces/{workspace_id}/members/{user_id}"
)
async def remove_member_api(
    workspace_id: str,
    user_id: str
):

    remove_member(
        workspace_id,
        user_id
    )

    return {
        "success": True
    }

# ============================================================
# 1D.18 LIST MEMBERS ENDPOINT
# ============================================================

@app.get(
    "/workspaces/{workspace_id}/members"
)
async def list_members_api(
    workspace_id: str
):

    return {
        "members":
            list_members(
                workspace_id
            )
    }

# ============================================================
# 1D.19 SETTINGS ENDPOINT
# ============================================================

@app.get(
    "/workspaces/{workspace_id}/settings"
)
async def workspace_settings_api(
    workspace_id: str
):

    return (
        WORKSPACE_SETTINGS.get(
            workspace_id
        )
    )

# ============================================================
# 1D.20 UPDATE SETTINGS ENDPOINT
# ============================================================

@app.put(
    "/workspaces/{workspace_id}/settings"
)
async def update_settings_api(
    workspace_id: str,
    settings:
    WorkspaceSettings
):

    update_workspace_settings(
        workspace_id,
        settings
    )

    return {
        "success": True
    }

# ============================================================
# PART 1D DELIVERABLE
#
# Workspace Model
# Workspace Members
# Workspace Settings
# Workspace Creation
# Workspace Retrieval
# Workspace Listing
# Member Management
# Settings Management
# Workspace APIs
#
# Ready For Part 1E
# ============================================================
# ============================================================
# ============================================================
# ============================================================
# SCRIPT 1
# PART 1E — CONVERSATIONS & CHAT STORAGE
# Paste directly below Part 1D
# ============================================================

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

# ============================================================
# 1E.1 CONVERSATION MODEL
# ============================================================

class Conversation(BaseModel):
    id: str
    workspace_id: str
    title: str
    created_by: str
    created_at: datetime
    updated_at: datetime

# ============================================================
# 1E.2 MESSAGE MODEL
# ============================================================

class Message(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: datetime

# ============================================================
# 1E.3 ATTACHMENT MODEL
# ============================================================

class Attachment(BaseModel):
    id: str
    message_id: str
    filename: str
    content_type: str
    created_at: datetime

# ============================================================
# 1E.4 STORAGE
# ============================================================

CONVERSATIONS = {}
MESSAGES = {}
ATTACHMENTS = {}

# ============================================================
# 1E.5 CREATE CONVERSATION REQUEST
# ============================================================

class CreateConversationRequest(
    BaseModel
):
    workspace_id: str
    title: str
    created_by: str

# ============================================================
# 1E.6 CREATE MESSAGE REQUEST
# ============================================================

class CreateMessageRequest(
    BaseModel
):
    conversation_id: str
    role: str
    content: str

# ============================================================
# 1E.7 CREATE CONVERSATION
# ============================================================

def create_conversation(
    workspace_id: str,
    title: str,
    created_by: str
):

    conversation_id = str(
        uuid.uuid4()
    )

    conversation = Conversation(
        id=conversation_id,
        workspace_id=workspace_id,
        title=title,
        created_by=created_by,
        created_at=
            datetime.utcnow(),
        updated_at=
            datetime.utcnow()
    )

    CONVERSATIONS[
        conversation_id
    ] = conversation

    MESSAGES[
        conversation_id
    ] = []

    return conversation

# ============================================================
# 1E.8 GET CONVERSATION
# ============================================================

def get_conversation(
    conversation_id: str
):

    return CONVERSATIONS.get(
        conversation_id
    )

# ============================================================
# 1E.9 LIST CONVERSATIONS
# ============================================================

def list_conversations(
    workspace_id: str
):

    return [
        conversation
        for conversation in
        CONVERSATIONS.values()
        if conversation.workspace_id
        == workspace_id
    ]

# ============================================================
# 1E.10 ADD MESSAGE
# ============================================================

def add_message(
    conversation_id: str,
    role: str,
    content: str
):

    message = Message(
        id=str(uuid.uuid4()),
        conversation_id=
            conversation_id,
        role=role,
        content=content,
        created_at=
            datetime.utcnow()
    )

    MESSAGES[
        conversation_id
    ].append(message)

    conversation = (
        CONVERSATIONS.get(
            conversation_id
        )
    )

    if conversation:
        conversation.updated_at = (
            datetime.utcnow()
        )

    return message

# ============================================================
# 1E.11 GET MESSAGES
# ============================================================

def get_messages(
    conversation_id: str
):

    return MESSAGES.get(
        conversation_id,
        []
    )

# ============================================================
# 1E.12 DELETE CONVERSATION
# ============================================================

def delete_conversation(
    conversation_id: str
):

    CONVERSATIONS.pop(
        conversation_id,
        None
    )

    MESSAGES.pop(
        conversation_id,
        None
    )

# ============================================================
# 1E.13 CREATE CONVERSATION ENDPOINT
# ============================================================

@app.post("/conversations")
async def create_conversation_api(
    request:
    CreateConversationRequest
):

    return create_conversation(
        request.workspace_id,
        request.title,
        request.created_by
    )

# ============================================================
# 1E.14 GET CONVERSATION ENDPOINT
# ============================================================

@app.get(
    "/conversations/{conversation_id}"
)
async def get_conversation_api(
    conversation_id: str
):

    return get_conversation(
        conversation_id
    )

# ============================================================
# 1E.15 LIST CONVERSATIONS ENDPOINT
# ============================================================

@app.get(
    "/workspaces/{workspace_id}/conversations"
)
async def list_conversations_api(
    workspace_id: str
):

    return {
        "conversations":
            list_conversations(
                workspace_id
            )
    }

# ============================================================
# 1E.16 ADD MESSAGE ENDPOINT
# ============================================================

@app.post(
    "/messages"
)
async def add_message_api(
    request:
    CreateMessageRequest
):

    return add_message(
        request.conversation_id,
        request.role,
        request.content
    )

# ============================================================
# 1E.17 GET MESSAGES ENDPOINT
# ============================================================

@app.get(
    "/conversations/{conversation_id}/messages"
)
async def get_messages_api(
    conversation_id: str
):

    return {
        "messages":
            get_messages(
                conversation_id
            )
    }

# ============================================================
# 1E.18 DELETE CONVERSATION ENDPOINT
# ============================================================

@app.delete(
    "/conversations/{conversation_id}"
)
async def delete_conversation_api(
    conversation_id: str
):

    delete_conversation(
        conversation_id
    )

    return {
        "success": True
    }

# ============================================================
# 1E.19 CHAT HISTORY SEARCH
# ============================================================

def search_messages(
    conversation_id: str,
    query: str
):

    results = []

    for message in get_messages(
        conversation_id
    ):
        if (
            query.lower()
            in message.content.lower()
        ):
            results.append(
                message
            )

    return results

# ============================================================
# 1E.20 SEARCH ENDPOINT
# ============================================================

@app.get(
    "/conversations/{conversation_id}/search"
)
async def search_messages_api(
    conversation_id: str,
    query: str
):

    return {
        "results":
            search_messages(
                conversation_id,
                query
            )
    }

# ============================================================
# PART 1E DELIVERABLE
#
# Conversation Model
# Message Model
# Attachment Model
# Conversation Creation
# Conversation Retrieval
# Conversation Listing
# Message Storage
# Chat History
# Search Functionality
# Conversation APIs
#
# Ready For Part 1F
# ============================================================
# ============================================================
# SCRIPT 1
# PART 1F — FILES, ATTACHMENTS & STORAGE
# Paste directly below Part 1E
# ============================================================

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
import os

# ============================================================
# 1F.1 FILE RECORD MODEL
# ============================================================

class FileRecord(BaseModel):
    id: str
    workspace_id: str
    uploaded_by: str
    filename: str
    content_type: str
    size_bytes: int
    path: str
    created_at: datetime

# ============================================================
# 1F.2 FILE PERMISSION MODEL
# ============================================================

class FilePermission(BaseModel):
    file_id: str
    user_id: str
    can_read: bool = True
    can_write: bool = False

# ============================================================
# 1F.3 STORAGE CONFIGURATION
# ============================================================

STORAGE_ROOT = "storage"

# ============================================================
# 1F.4 STORAGE TABLES
# ============================================================

FILES = {}
FILE_PERMISSIONS = {}

# ============================================================
# 1F.5 STORAGE INITIALIZATION
# ============================================================

def initialize_storage():

    os.makedirs(
        STORAGE_ROOT,
        exist_ok=True
    )

# ============================================================
# 1F.6 CREATE FILE RECORD
# ============================================================

def create_file_record(
    workspace_id: str,
    uploaded_by: str,
    filename: str,
    content_type: str,
    size_bytes: int,
    path: str
):

    file_record = FileRecord(
        id=str(uuid.uuid4()),
        workspace_id=workspace_id,
        uploaded_by=uploaded_by,
        filename=filename,
        content_type=content_type,
        size_bytes=size_bytes,
        path=path,
        created_at=
            datetime.utcnow()
    )

    FILES[
        file_record.id
    ] = file_record

    return file_record

# ============================================================
# 1F.7 GET FILE
# ============================================================

def get_file(
    file_id: str
):

    return FILES.get(
        file_id
    )

# ============================================================
# 1F.8 DELETE FILE
# ============================================================

def delete_file(
    file_id: str
):

    file_record = (
        FILES.get(file_id)
    )

    if not file_record:
        return False

    if os.path.exists(
        file_record.path
    ):
        os.remove(
            file_record.path
        )

    FILES.pop(
        file_id,
        None
    )

    return True

# ============================================================
# 1F.9 LIST FILES
# ============================================================

def list_workspace_files(
    workspace_id: str
):

    return [
        file_record
        for file_record
        in FILES.values()
        if file_record.workspace_id
        == workspace_id
    ]

# ============================================================
# 1F.10 GRANT PERMISSION
# ============================================================

def grant_file_access(
    file_id: str,
    user_id: str,
    can_read: bool = True,
    can_write: bool = False
):

    permission = (
        FilePermission(
            file_id=file_id,
            user_id=user_id,
            can_read=can_read,
            can_write=can_write
        )
    )

    FILE_PERMISSIONS[
        f"{file_id}:{user_id}"
    ] = permission

    return permission

# ============================================================
# 1F.11 CHECK ACCESS
# ============================================================

def has_file_access(
    file_id: str,
    user_id: str
):

    permission = (
        FILE_PERMISSIONS.get(
            f"{file_id}:{user_id}"
        )
    )

    if not permission:
        return False

    return permission.can_read

# ============================================================
# 1F.12 FILE METADATA
# ============================================================

def file_metadata(
    file_id: str
):

    file_record = (
        get_file(file_id)
    )

    if not file_record:
        return None

    return {
        "id":
            file_record.id,
        "filename":
            file_record.filename,
        "content_type":
            file_record.content_type,
        "size_bytes":
            file_record.size_bytes,
        "created_at":
            file_record.created_at
    }

# ============================================================
# 1F.13 FILE SEARCH
# ============================================================

def search_files(
    workspace_id: str,
    query: str
):

    results = []

    for file_record in (
        list_workspace_files(
            workspace_id
        )
    ):
        if (
            query.lower()
            in file_record.filename
            .lower()
        ):
            results.append(
                file_record
            )

    return results

# ============================================================
# 1F.14 FILE INFO ENDPOINT
# ============================================================

@app.get("/files/{file_id}")
async def file_info_api(
    file_id: str
):

    return file_metadata(
        file_id
    )

# ============================================================
# 1F.15 FILE LIST ENDPOINT
# ============================================================

@app.get(
    "/workspaces/{workspace_id}/files"
)
async def file_list_api(
    workspace_id: str
):

    return {
        "files":
            list_workspace_files(
                workspace_id
            )
    }

# ============================================================
# 1F.16 FILE DELETE ENDPOINT
# ============================================================

@app.delete(
    "/files/{file_id}"
)
async def delete_file_api(
    file_id: str
):

    return {
        "success":
            delete_file(
                file_id
            )
    }

# ============================================================
# 1F.17 FILE SEARCH ENDPOINT
# ============================================================

@app.get(
    "/workspaces/{workspace_id}/files/search"
)
async def search_files_api(
    workspace_id: str,
    query: str
):

    return {
        "results":
            search_files(
                workspace_id,
                query
            )
    }

# ============================================================
# 1F.18 STORAGE HEALTH CHECK
# ============================================================

@app.get("/storage/health")
async def storage_health():

    return {
        "status": "healthy",
        "storage_root":
            STORAGE_ROOT
    }

# ============================================================
# 1F.19 STORAGE STATS
# ============================================================

def storage_stats():

    total_files = len(
        FILES
    )

    total_size = sum(
        file.size_bytes
        for file in
        FILES.values()
    )

    return {
        "total_files":
            total_files,
        "total_size":
            total_size
    }

# ============================================================
# 1F.20 STORAGE STATS ENDPOINT
# ============================================================

@app.get("/storage/stats")
async def storage_stats_api():

    return storage_stats()

# ============================================================
# PART 1F DELIVERABLE
#
# File Storage
# File Records
# File Permissions
# File Metadata
# File Search
# File Deletion
# Workspace File Listing
# Storage Statistics
# Storage Health Checks
# Attachment Foundation
#
# Ready For Script 2 Part 2A
# ============================================================
