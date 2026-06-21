# =========================================================
# PART 1A
# FOUNDATION + CONFIGURATION + DATABASE
# Bloxy-Bot X
# =========================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sqlite3
import uuid
import hashlib
import secrets
import os
from datetime import datetime

# =========================================================
# APP SETUP
# =========================================================

app = FastAPI(
    title="Bloxy-Bot X",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# =========================================================
# CONFIGURATION
# =========================================================

DB_NAME = os.getenv(
    "DATABASE_NAME",
    "bloxybotx.db"
)

APP_NAME = "Bloxy-Bot X"

OWNER_USERNAME = "aTg"

OWNER_EMAILS = [
    "alvinogthegreat177@gmail.com",
    "alvinogthegreat177@outlook.com"
]

# =========================================================
# HELPERS
# =========================================================

def generate_id():
    return str(uuid.uuid4())

def generate_token():
    return secrets.token_hex(32)

def now():
    return datetime.utcnow().isoformat()

def hash_password(password: str):
    return hashlib.sha256(
        password.encode()
    ).hexdigest()

# =========================================================
# DATABASE
# =========================================================

def get_db():
    conn = sqlite3.connect(
        DB_NAME
    )
    conn.row_factory = sqlite3.Row
    return conn

# =========================================================
# DATABASE TABLES
# =========================================================

def create_tables():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        password TEXT,
        verified INTEGER DEFAULT 0,
        role TEXT DEFAULT 'user',
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions(
        token TEXT PRIMARY KEY,
        user_id TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_badges(
        id TEXT PRIMARY KEY,
        user_id TEXT,
        badge_type TEXT,
        badge_color TEXT,
        granted_by TEXT,
        granted_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings(
        user_id TEXT PRIMARY KEY,
        theme TEXT DEFAULT 'dark',
        model TEXT DEFAULT 'gpt-4o-mini',
        updated_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs(
        id TEXT PRIMARY KEY,
        user_id TEXT,
        action TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

# =========================================================
# AUDIT LOGGING
# =========================================================

def create_audit_log(
    user_id,
    action
):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO audit_logs
        VALUES(?,?,?,?)
        """,
        (
            generate_id(),
            user_id,
            action,
            now()
        )
    )

    conn.commit()
    conn.close()

# =========================================================
# OWNER BOOTSTRAP
# =========================================================

def owner_exists():
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM users
        WHERE role='super_admin'
        LIMIT 1
        """
    )

    row = cur.fetchone()

    conn.close()
    return row

def create_owner():

    if owner_exists():
        return

    owner_id = generate_id()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO users
        VALUES(?,?,?,?,?,?,?)
        """,
        (
            owner_id,
            OWNER_USERNAME,
            OWNER_EMAILS[0],
            hash_password("CHANGE_ME"),
            1,
            "super_admin",
            now()
        )
    )

    cur.execute(
        """
        INSERT INTO user_badges
        VALUES(?,?,?,?,?,?)
        """,
        (
            generate_id(),
            owner_id,
            "owner",
            "#ff8c00",
            owner_id,
            now()
        )
    )

    conn.commit()
    conn.close()

# =========================================================
# SYSTEM STARTUP
# =========================================================

create_tables()
create_owner()

# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():
    return {
        "success": True,
        "app": APP_NAME,
        "status": "online",
        "timestamp": now()
    }

# =========================================================
# SYSTEM INFO
# =========================================================

@app.get("/api/system/info")
def system_info():
    return {
        "success": True,
        "app": APP_NAME,
        "version": "2.0.0",
        "database": DB_NAME
    }

# =========================================================
# PART 1A COMPLETE
# NEXT:
# PART 1B = AUTHENTICATION + VERIFICATION
# =========================================================
# =========================================================
# PART 1B
# AUTHENTICATION + EMAIL VERIFICATION
# PASTE BELOW PART 1A
# =========================================================

from pydantic import EmailStr

# =========================================================
# REQUEST MODELS
# =========================================================

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class VerifyEmailRequest(BaseModel):
    token: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

# =========================================================
# AUTH TABLES
# =========================================================

def create_auth_tables():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS email_verifications(
        token TEXT PRIMARY KEY,
        user_id TEXT,
        email TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS password_resets(
        token TEXT PRIMARY KEY,
        user_id TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_auth_tables()

# =========================================================
# USER HELPERS
# =========================================================

def get_user_by_email(email):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE email=?",
        (email,)
    )

    row = cur.fetchone()
    conn.close()
    return row

def get_user_by_id(user_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE id=?",
        (user_id,)
    )

    row = cur.fetchone()
    conn.close()
    return row

# =========================================================
# SESSION HELPERS
# =========================================================

def create_session(user_id):
    token = generate_token()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO sessions VALUES(?,?,?)",
        (
            token,
            user_id,
            now()
        )
    )

    conn.commit()
    conn.close()

    return token

def get_session(token):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM sessions WHERE token=?",
        (token,)
    )

    row = cur.fetchone()
    conn.close()

    return row

# =========================================================
# TOKEN HELPERS
# =========================================================

def create_verification_token(
    user_id,
    email
):
    token = generate_token()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO email_verifications
        VALUES(?,?,?,?)
        """,
        (
            token,
            user_id,
            email,
            now()
        )
    )

    conn.commit()
    conn.close()

    return token

def create_password_reset_token(
    user_id
):
    token = generate_token()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO password_resets
        VALUES(?,?,?)
        """,
        (
            token,
            user_id,
            now()
        )
    )

    conn.commit()
    conn.close()

    return token

# =========================================================
# REGISTER
# =========================================================

@app.post("/api/register")
def register(data: RegisterRequest):

    if get_user_by_email(data.email):
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "Email already exists"
            }
        )

    user_id = generate_id()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO users
        VALUES(?,?,?,?,?,?,?)
        """,
        (
            user_id,
            data.username,
            data.email,
            hash_password(data.password),
            0,
            "user",
            now()
        )
    )

    conn.commit()
    conn.close()

    verification_token = (
        create_verification_token(
            user_id,
            data.email
        )
    )

    create_audit_log(
        user_id,
        "user_registered"
    )

    return {
        "success": True,
        "user_id": user_id,
        "verification_token":
            verification_token
    }

# =========================================================
# LOGIN
# =========================================================

@app.post("/api/login")
def login(data: LoginRequest):

    user = get_user_by_email(
        data.email
    )

    if (
        not user or
        user["password"] !=
        hash_password(data.password)
    ):
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "message":
                "Invalid credentials"
            }
        )

    token = create_session(
        user["id"]
    )

    create_audit_log(
        user["id"],
        "user_login"
    )

    return {
        "success": True,
        "token": token,
        "user_id": user["id"]
    }

# =========================================================
# LOGOUT
# =========================================================

@app.delete("/api/logout/{token}")
def logout(token: str):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM sessions WHERE token=?",
        (token,)
    )

    conn.commit()
    conn.close()

    return {"success": True}

# =========================================================
# VERIFY EMAIL
# =========================================================

@app.post("/api/verify-email")
def verify_email(
    data: VerifyEmailRequest
):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM email_verifications
        WHERE token=?
        """,
        (data.token,)
    )

    row = cur.fetchone()

    if not row:
        conn.close()
        return {
            "success": False,
            "message": "Invalid token"
        }

    cur.execute(
        """
        UPDATE users
        SET verified=1
        WHERE id=?
        """,
        (row["user_id"],)
    )

    cur.execute(
        """
        DELETE FROM email_verifications
        WHERE token=?
        """,
        (data.token,)
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Email verified"
    }

# =========================================================
# FORGOT PASSWORD
# =========================================================

@app.post("/api/forgot-password")
def forgot_password(
    data: ForgotPasswordRequest
):
    user = get_user_by_email(
        data.email
    )

    if not user:
        return {"success": True}

    token = create_password_reset_token(
        user["id"]
    )

    return {
        "success": True,
        "reset_token": token
    }

# =========================================================
# RESET PASSWORD
# =========================================================

@app.post("/api/reset-password")
def reset_password(
    data: ResetPasswordRequest
):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM password_resets
        WHERE token=?
        """,
        (data.token,)
    )

    row = cur.fetchone()

    if not row:
        conn.close()
        return {
            "success": False,
            "message": "Invalid token"
        }

    cur.execute(
        """
        UPDATE users
        SET password=?
        WHERE id=?
        """,
        (
            hash_password(
                data.new_password
            ),
            row["user_id"]
        )
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Password updated"
    }

# =========================================================
# PART 1B COMPLETE
# NEXT:
# PART 1C = PROFILES + ROLES + VERIFICATION
# =========================================================
# =========================================================
# PART 1C
# PROFILES + ROLES + VERIFICATION SYSTEM
# PASTE BELOW PART 1B
# =========================================================

from enum import Enum

# =========================================================
# USER ROLES
# =========================================================

class UserRole(str, Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"
    OWNER = "owner"
    SUPER_ADMIN = "super_admin"

# =========================================================
# VERIFICATION TYPES
# =========================================================

class VerificationType(str, Enum):
    NONE = "none"
    ORANGE = "orange"

# =========================================================
# DATABASE UPGRADE
# =========================================================

def upgrade_user_table():

    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            ALTER TABLE users
            ADD COLUMN display_name TEXT
            """
        )
    except:
        pass

    try:
        cur.execute(
            """
            ALTER TABLE users
            ADD COLUMN bio TEXT
            """
        )
    except:
        pass

    try:
        cur.execute(
            """
            ALTER TABLE users
            ADD COLUMN verification_type TEXT
            DEFAULT 'none'
            """
        )
    except:
        pass

    conn.commit()
    conn.close()

upgrade_user_table()

# =========================================================
# PROFILE REQUEST MODELS
# =========================================================

class UpdateProfileRequest(BaseModel):
    user_id: str
    display_name: str = ""
    bio: str = ""

# =========================================================
# VERIFICATION HELPERS
# =========================================================

OWNER_EMAILS = {
    "alvinogthegreat177@gmail.com",
    "alvinogthegreat177@outlook.com"
}

def assign_special_badge(user):

    if user["email"] in OWNER_EMAILS:
        return {
            "role":
                UserRole.OWNER,
            "verified":
                1,
            "verification_type":
                VerificationType.ORANGE
        }

    return {
        "role":
            UserRole.USER,
        "verified":
            0,
        "verification_type":
            VerificationType.NONE
    }

def verification_tooltip(role):

    if role in [
        UserRole.OWNER,
        UserRole.SUPER_ADMIN
    ]:
        return (
            "This badge belongs to the "
            "rightful owner of the platform."
        )

    if role in [
        UserRole.ADMIN,
        UserRole.MODERATOR
    ]:
        return (
            "This badge belongs to an "
            "administrator or contributor."
        )

    return ""

# =========================================================
# PUBLIC USER FORMATTER
# =========================================================

def public_user(user):

    return {
        "id":
            user["id"],
        "username":
            user["username"],
        "display_name":
            user["display_name"],
        "bio":
            user["bio"],
        "role":
            user["role"],
        "verified":
            bool(user["verified"]),
        "verification_type":
            user["verification_type"],
        "verification_tooltip":
            verification_tooltip(
                user["role"]
            )
    }

# =========================================================
# PROFILE ENDPOINTS
# =========================================================

@app.get("/api/profile/{user_id}")
def get_profile(
    user_id: str
):
    user = get_user_by_id(
        user_id
    )

    if not user:
        return {
            "success": False,
            "message":
            "User not found"
        }

    return {
        "success": True,
        "user":
        public_user(user)
    }

@app.post("/api/profile/update")
def update_profile(
    data: UpdateProfileRequest
):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE users
        SET display_name=?,
            bio=?
        WHERE id=?
        """,
        (
            data.display_name,
            data.bio,
            data.user_id
        )
    )

    conn.commit()
    conn.close()

    create_audit_log(
        data.user_id,
        "profile_updated"
    )

    return {
        "success": True
    }

# =========================================================
# STAFF BADGE HELPER
# =========================================================

def grant_staff_badge(
    user_id,
    role="admin"
):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE users
        SET role=?,
            verified=1,
            verification_type='orange'
        WHERE id=?
        """,
        (
            role,
            user_id
        )
    )

    conn.commit()
    conn.close()

    return True

# =========================================================
# PART 1C COMPLETE
# NEXT:
# PART 1D
# ADMIN SYSTEM + BADGES + AUDIT LOGS
# =========================================================
# =========================================================
# PART 1D
# ADMIN SYSTEM + BADGES + AUDIT LOGS
# PASTE BELOW PART 1C
# =========================================================

# =========================================================
# REQUEST MODELS
# =========================================================

class GrantBadgeRequest(BaseModel):
    admin_user_id: str
    target_user_id: str
    role: str = "admin"

class RevokeBadgeRequest(BaseModel):
    admin_user_id: str
    target_user_id: str

# =========================================================
# PERMISSION HELPERS
# =========================================================

def is_admin(user_id):

    user = get_user_by_id(
        user_id
    )

    if not user:
        return False

    return user["role"] in [
        "super_admin",
        "owner",
        "admin"
    ]

def is_owner(user_id):

    user = get_user_by_id(
        user_id
    )

    if not user:
        return False

    return user["role"] in [
        "super_admin",
        "owner"
    ]

# =========================================================
# GRANT STAFF BADGE
# =========================================================

@app.post("/api/admin/grant-badge")
def grant_badge(
    data: GrantBadgeRequest
):

    if not is_owner(
        data.admin_user_id
    ):
        return {
            "success": False,
            "message":
            "Owner permission required"
        }

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE users
        SET role=?,
            verified=1,
            verification_type='orange'
        WHERE id=?
        """,
        (
            data.role,
            data.target_user_id
        )
    )

    cur.execute(
        """
        INSERT INTO user_badges
        VALUES(?,?,?,?,?,?)
        """,
        (
            generate_id(),
            data.target_user_id,
            data.role,
            "#ff8c00",
            data.admin_user_id,
            now()
        )
    )

    conn.commit()
    conn.close()

    create_audit_log(
        data.admin_user_id,
        f"grant_{data.role}"
    )

    return {
        "success": True,
        "role": data.role,
        "badge": "orange_checkmark"
    }

# =========================================================
# REVOKE STAFF BADGE
# =========================================================

@app.post("/api/admin/revoke-badge")
def revoke_badge(
    data: RevokeBadgeRequest
):

    if not is_owner(
        data.admin_user_id
    ):
        return {
            "success": False,
            "message":
            "Owner permission required"
        }

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE users
        SET role='user',
            verified=0,
            verification_type='none'
        WHERE id=?
        """,
        (
            data.target_user_id,
        )
    )

    cur.execute(
        """
        DELETE FROM user_badges
        WHERE user_id=?
        """,
        (
            data.target_user_id,
        )
    )

    conn.commit()
    conn.close()

    create_audit_log(
        data.admin_user_id,
        "revoke_badge"
    )

    return {
        "success": True
    }

# =========================================================
# LIST STAFF
# =========================================================

@app.get("/api/admin/staff")
def list_staff():

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
            username,
            display_name,
            email,
            role,
            verified
        FROM users
        WHERE role != 'user'
        ORDER BY role
        """
    )

    staff = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "staff": staff
    }

# =========================================================
# AUDIT LOGS
# =========================================================

@app.get("/api/admin/audit")
def audit_logs():

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM audit_logs
        ORDER BY created_at DESC
        LIMIT 500
        """
    )

    logs = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "logs": logs
    }

# =========================================================
# BADGE TOOLTIP
# =========================================================

@app.get("/api/badge-tooltip/{user_id}")
def badge_tooltip(
    user_id: str
):

    user = get_user_by_id(
        user_id
    )

    if not user:
        return {
            "success": False
        }

    return {
        "success": True,
        "tooltip":
            verification_tooltip(
                user["role"]
            ),
        "verification_type":
            user["verification_type"]
    }

# =========================================================
# PLATFORM HEALTH
# =========================================================

@app.get("/api/system/health")
def system_health():

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM users"
    )
    total_users = (
        cur.fetchone()[0]
    )

    cur.execute(
        "SELECT COUNT(*) FROM sessions"
    )
    active_sessions = (
        cur.fetchone()[0]
    )

    cur.execute(
        "SELECT COUNT(*) FROM audit_logs"
    )
    audit_entries = (
        cur.fetchone()[0]
    )

    conn.close()

    return {
        "success": True,
        "app": APP_NAME,
        "status": "online",
        "users": total_users,
        "active_sessions":
            active_sessions,
        "audit_entries":
            audit_entries,
        "timestamp": now()
    }

# =========================================================
# PART 1 COMPLETE
# NEXT:
# PART 2A
# CONVERSATIONS + CHAT FOUNDATION
# =========================================================
# =========================================================
# PART 2A
# CONVERSATIONS + CHAT FOUNDATION
# PASTE BELOW PART 1D
# =========================================================

# =========================================================
# REQUEST MODELS
# =========================================================

class CreateConversationRequest(BaseModel):
    user_id: str
    title: str = "New Chat"

class RenameConversationRequest(BaseModel):
    conversation_id: str
    title: str

class DeleteConversationRequest(BaseModel):
    conversation_id: str

class MessageRequest(BaseModel):
    conversation_id: str
    user_id: str
    message: str

# =========================================================
# CONVERSATION TABLES
# =========================================================

def create_conversation_tables():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS conversations(
        id TEXT PRIMARY KEY,
        user_id TEXT,
        title TEXT,
        pinned INTEGER DEFAULT 0,
        archived INTEGER DEFAULT 0,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages(
        id TEXT PRIMARY KEY,
        conversation_id TEXT,
        user_id TEXT,
        role TEXT,
        content TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_conversation_tables()

# =========================================================
# HELPERS
# =========================================================

def get_conversation(
    conversation_id
):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM conversations
        WHERE id=?
        """,
        (conversation_id,)
    )

    row = cur.fetchone()

    conn.close()
    return row

def conversation_exists(
    conversation_id
):
    return bool(
        get_conversation(
            conversation_id
        )
    )

# =========================================================
# CREATE CONVERSATION
# =========================================================

@app.post(
    "/api/conversations/create"
)
def create_conversation(
    data: CreateConversationRequest
):

    conversation_id = generate_id()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO conversations
        VALUES(?,?,?,?,?,?,?)
        """,
        (
            conversation_id,
            data.user_id,
            data.title,
            0,
            0,
            now(),
            now()
        )
    )

    conn.commit()
    conn.close()

    create_audit_log(
        data.user_id,
        "conversation_created"
    )

    return {
        "success": True,
        "conversation_id":
            conversation_id
    }

# =========================================================
# LIST CONVERSATIONS
# =========================================================

@app.get(
    "/api/conversations/{user_id}"
)
def get_conversations(
    user_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM conversations
        WHERE user_id=?
        ORDER BY updated_at DESC
        """,
        (user_id,)
    )

    conversations = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "conversations":
            conversations
    }

# =========================================================
# RENAME CONVERSATION
# =========================================================

@app.post(
    "/api/conversations/rename"
)
def rename_conversation(
    data: RenameConversationRequest
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE conversations
        SET title=?,
            updated_at=?
        WHERE id=?
        """,
        (
            data.title,
            now(),
            data.conversation_id
        )
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# PIN CONVERSATION
# =========================================================

@app.post(
    "/api/conversations/pin/{conversation_id}"
)
def pin_conversation(
    conversation_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE conversations
        SET pinned=1
        WHERE id=?
        """,
        (conversation_id,)
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# ARCHIVE CONVERSATION
# =========================================================

@app.post(
    "/api/conversations/archive/{conversation_id}"
)
def archive_conversation(
    conversation_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE conversations
        SET archived=1
        WHERE id=?
        """,
        (conversation_id,)
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# DELETE CONVERSATION
# =========================================================

@app.delete(
    "/api/conversations/delete/{conversation_id}"
)
def delete_conversation(
    conversation_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM messages
        WHERE conversation_id=?
        """,
        (conversation_id,)
    )

    cur.execute(
        """
        DELETE FROM conversations
        WHERE id=?
        """,
        (conversation_id,)
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# SAVE MESSAGE
# =========================================================

def save_message(
    conversation_id,
    user_id,
    role,
    content
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO messages
        VALUES(?,?,?,?,?,?)
        """,
        (
            generate_id(),
            conversation_id,
            user_id,
            role,
            content,
            now()
        )
    )

    cur.execute(
        """
        UPDATE conversations
        SET updated_at=?
        WHERE id=?
        """,
        (
            now(),
            conversation_id
        )
    )

    conn.commit()
    conn.close()

# =========================================================
# SEND MESSAGE
# =========================================================

@app.post(
    "/api/messages/send"
)
def send_message(
    data: MessageRequest
):

    if not conversation_exists(
        data.conversation_id
    ):
        return {
            "success": False,
            "message":
            "Conversation not found"
        }

    save_message(
        data.conversation_id,
        data.user_id,
        "user",
        data.message
    )

    return {
        "success": True
    }

# =========================================================
# GET MESSAGES
# =========================================================

@app.get(
    "/api/messages/{conversation_id}"
)
def get_messages(
    conversation_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM messages
        WHERE conversation_id=?
        ORDER BY created_at ASC
        """,
        (conversation_id,)
    )

    messages = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "messages":
            messages
    }

# =========================================================
# CONVERSATION STATS
# =========================================================

@app.get(
    "/api/conversations/stats/{conversation_id}"
)
def conversation_stats(
    conversation_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT COUNT(*)
        FROM messages
        WHERE conversation_id=?
        """,
        (conversation_id,)
    )

    count = cur.fetchone()[0]

    conn.close()

    return {
        "success": True,
        "message_count":
            count
    }

# =========================================================
# PART 2A COMPLETE
# NEXT:
# PART 2B
# MESSAGE HISTORY + SEARCH + EXPORT
# =========================================================
# =========================================================
# PART 2B
# ADVANCED MESSAGE HISTORY + SEARCH + EXPORT
# =========================================================

import json

class SearchMessagesRequest(BaseModel):
    conversation_id: str
    query: str

# =========================================================
# SEARCH MESSAGES
# =========================================================
@app.post("/api/messages/search")
def search_messages(data: SearchMessagesRequest):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM messages
        WHERE conversation_id=?
        AND content LIKE ?
        ORDER BY created_at DESC
        """,
        (
            data.conversation_id,
            f"%{data.query}%"
        )
    )

    results = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "count": len(results),
        "results": results
    }

# =========================================================
# DELETE MESSAGE
# =========================================================
@app.delete("/api/messages/{message_id}")
def delete_message(message_id: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM messages
        WHERE id=?
        """,
        (message_id,)
    )

    conn.commit()
    conn.close()

    return {"success": True}

# =========================================================
# EXPORT CONVERSATION
# =========================================================
@app.get(
    "/api/conversations/export/{conversation_id}"
)
def export_conversation(
    conversation_id: str
):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM conversations
        WHERE id=?
        """,
        (conversation_id,)
    )

    conversation = cur.fetchone()

    if not conversation:
        conn.close()
        return {
            "success": False,
            "message":
            "Conversation not found"
        }

    cur.execute(
        """
        SELECT *
        FROM messages
        WHERE conversation_id=?
        ORDER BY created_at ASC
        """,
        (conversation_id,)
    )

    messages = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "conversation":
            dict(conversation),
        "messages":
            messages,
        "exported_at": now()
    }

# =========================================================
# CLEAR CONVERSATION
# =========================================================
@app.delete(
    "/api/conversations/clear/{conversation_id}"
)
def clear_conversation(
    conversation_id: str
):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM messages
        WHERE conversation_id=?
        """,
        (conversation_id,)
    )

    conn.commit()
    conn.close()

    return {"success": True}

# =========================================================
# PART 2B COMPLETE
# NEXT:
# PART 2C
# AI RESPONSES + MODEL MANAGEMENT
# =========================================================
# =========================================================
# PART 2C
# AI RESPONSES + MODEL MANAGEMENT + CHAT COMPLETIONS
# =========================================================

# =========================================================
# REQUEST MODELS
# =========================================================

class AIMessageRequest(BaseModel):
    conversation_id: str
    user_id: str
    message: str
    model: str = "gpt-4o-mini"

# =========================================================
# SUPPORTED MODELS
# =========================================================

SUPPORTED_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4.1",
    "gpt-4.1-mini"
]

# =========================================================
# MODEL VALIDATION
# =========================================================

def valid_model(model):
    return model in SUPPORTED_MODELS

# =========================================================
# AI ENGINE
# REPLACE WITH OPENAI API
# =========================================================

def generate_ai_response(
    user_message,
    model
):
    return (
        f"[{model}] "
        f"Response to: {user_message}"
    )

# =========================================================
# SAVE ASSISTANT MESSAGE
# =========================================================

def save_assistant_message(
    conversation_id,
    content
):
    save_message(
        conversation_id,
        "assistant",
        "assistant",
        content
    )

# =========================================================
# CHAT COMPLETION
# =========================================================

@app.post("/api/chat/completion")
def chat_completion(
    data: AIMessageRequest
):

    if not conversation_exists(
        data.conversation_id
    ):
        return {
            "success": False,
            "message":
            "Conversation not found"
        }

    if not valid_model(
        data.model
    ):
        return {
            "success": False,
            "message":
            "Unsupported model"
        }

    save_message(
        data.conversation_id,
        data.user_id,
        "user",
        data.message
    )

    ai_response = (
        generate_ai_response(
            data.message,
            data.model
        )
    )

    save_assistant_message(
        data.conversation_id,
        ai_response
    )

    create_audit_log(
        data.user_id,
        "ai_completion"
    )

    return {
        "success": True,
        "model": data.model,
        "response": ai_response
    }

# =========================================================
# LIST MODELS
# =========================================================

@app.get("/api/models")
def list_models():
    return {
        "success": True,
        "models":
        SUPPORTED_MODELS
    }

# =========================================================
# CONVERSATION CONTEXT
# =========================================================

@app.get(
    "/api/chat/context/{conversation_id}"
)
def conversation_context(
    conversation_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT role,content
        FROM messages
        WHERE conversation_id=?
        ORDER BY created_at ASC
        LIMIT 100
        """,
        (conversation_id,)
    )

    rows = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "context": rows
    }

# =========================================================
# TOKEN ESTIMATION
# =========================================================

@app.get(
    "/api/chat/tokens/{conversation_id}"
)
def estimate_tokens(
    conversation_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT content
        FROM messages
        WHERE conversation_id=?
        """,
        (conversation_id,)
    )

    total = 0

    for row in cur.fetchall():
        total += len(
            row["content"].split()
        )

    conn.close()

    return {
        "success": True,
        "estimated_tokens":
            total
    }

# =========================================================
# REGENERATE RESPONSE
# =========================================================

@app.post(
    "/api/chat/regenerate/{conversation_id}"
)
def regenerate_response(
    conversation_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM messages
        WHERE conversation_id=?
        AND role='user'
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (conversation_id,)
    )

    last_user = cur.fetchone()

    conn.close()

    if not last_user:
        return {
            "success": False
        }

    ai_response = (
        generate_ai_response(
            last_user["content"],
            "gpt-4o-mini"
        )
    )

    save_assistant_message(
        conversation_id,
        ai_response
    )

    return {
        "success": True,
        "response": ai_response
    }

# =========================================================
# PART 2C COMPLETE
# NEXT:
# PART 2D
# CHAT EXPORT + IMPORT
# =========================================================
# =========================================================
# PART 2D
# CHAT EXPORT + IMPORT
# PASTE BELOW PART 2C
# =========================================================

import json

# =========================================================
# IMPORT REQUEST MODEL
# =========================================================

class ImportConversationRequest(
    BaseModel
):
    user_id: str
    title: str
    messages: list

# =========================================================
# EXPORT CONVERSATION
# =========================================================

@app.get(
    "/api/conversations/export/{conversation_id}"
)
def export_conversation(
    conversation_id: str
):

    conversation = get_conversation(
        conversation_id
    )

    if not conversation:
        return {
            "success": False,
            "message":
            "Conversation not found"
        }

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM messages
        WHERE conversation_id=?
        ORDER BY created_at ASC
        """,
        (conversation_id,)
    )

    messages = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "conversation":
            dict(conversation),
        "messages":
            messages,
        "exported_at":
            now()
    }

# =========================================================
# IMPORT CONVERSATION
# =========================================================

@app.post(
    "/api/conversations/import"
)
def import_conversation(
    data: ImportConversationRequest
):

    conversation_id = generate_id()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO conversations
        VALUES(?,?,?,?,?,?,?)
        """,
        (
            conversation_id,
            data.user_id,
            data.title,
            0,
            0,
            now(),
            now()
        )
    )

    for msg in data.messages:

        cur.execute(
            """
            INSERT INTO messages
            VALUES(?,?,?,?,?,?)
            """,
            (
                generate_id(),
                conversation_id,
                msg.get(
                    "user_id",
                    data.user_id
                ),
                msg.get(
                    "role",
                    "user"
                ),
                msg.get(
                    "content",
                    ""
                ),
                msg.get(
                    "created_at",
                    now()
                )
            )
        )

    conn.commit()
    conn.close()

    create_audit_log(
        data.user_id,
        "conversation_imported"
    )

    return {
        "success": True,
        "conversation_id":
            conversation_id
    }

# =========================================================
# DUPLICATE CONVERSATION
# =========================================================

@app.post(
    "/api/conversations/duplicate/{conversation_id}"
)
def duplicate_conversation(
    conversation_id: str
):

    original = get_conversation(
        conversation_id
    )

    if not original:
        return {
            "success": False
        }

    conn = get_db()
    cur = conn.cursor()

    new_id = generate_id()

    cur.execute(
        """
        INSERT INTO conversations
        VALUES(?,?,?,?,?,?,?)
        """,
        (
            new_id,
            original["user_id"],
            f"{original['title']} Copy",
            0,
            0,
            now(),
            now()
        )
    )

    cur.execute(
        """
        SELECT *
        FROM messages
        WHERE conversation_id=?
        ORDER BY created_at ASC
        """,
        (conversation_id,)
    )

    for msg in cur.fetchall():

        cur.execute(
            """
            INSERT INTO messages
            VALUES(?,?,?,?,?,?)
            """,
            (
                generate_id(),
                new_id,
                msg["user_id"],
                msg["role"],
                msg["content"],
                msg["created_at"]
            )
        )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "conversation_id":
            new_id
    }

# =========================================================
# CLEAR CONVERSATION
# =========================================================

@app.delete(
    "/api/conversations/clear/{conversation_id}"
)
def clear_conversation(
    conversation_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM messages
        WHERE conversation_id=?
        """,
        (conversation_id,)
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# PART 2D COMPLETE
# NEXT:
# PART 2E
# CHAT SHARING + FAVORITES + FOLDERS
# =========================================================
# =========================================================
# PART 2E
# CHAT SHARING + FAVORITES + FOLDERS
# PASTE BELOW PART 2D
# =========================================================

# =========================================================
# TABLES
# =========================================================

def create_organization_tables():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS folders(
        id TEXT PRIMARY KEY,
        user_id TEXT,
        name TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS shared_chats(
        id TEXT PRIMARY KEY,
        conversation_id TEXT,
        share_token TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_organization_tables()

# =========================================================
# REQUEST MODELS
# =========================================================

class CreateFolderRequest(BaseModel):
    user_id: str
    name: str

class MoveConversationRequest(BaseModel):
    conversation_id: str
    folder_id: str

# =========================================================
# ADD OPTIONAL COLUMNS
# =========================================================

try:
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "ALTER TABLE conversations ADD COLUMN folder_id TEXT"
    )

    cur.execute(
        "ALTER TABLE conversations ADD COLUMN favorite INTEGER DEFAULT 0"
    )

    conn.commit()
    conn.close()

except:
    pass

# =========================================================
# FAVORITE CONVERSATION
# =========================================================

@app.post(
    "/api/conversations/favorite/{conversation_id}"
)
def favorite_conversation(
    conversation_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE conversations
        SET favorite=1
        WHERE id=?
        """,
        (conversation_id,)
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# CREATE FOLDER
# =========================================================

@app.post("/api/folders/create")
def create_folder(
    data: CreateFolderRequest
):

    folder_id = generate_id()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO folders
        VALUES(?,?,?,?)
        """,
        (
            folder_id,
            data.user_id,
            data.name,
            now()
        )
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "folder_id": folder_id
    }

# =========================================================
# LIST FOLDERS
# =========================================================

@app.get("/api/folders/{user_id}")
def list_folders(
    user_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM folders
        WHERE user_id=?
        ORDER BY name ASC
        """,
        (user_id,)
    )

    folders = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "folders": folders
    }

# =========================================================
# MOVE CONVERSATION
# =========================================================

@app.post("/api/conversations/move")
def move_conversation(
    data: MoveConversationRequest
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE conversations
        SET folder_id=?
        WHERE id=?
        """,
        (
            data.folder_id,
            data.conversation_id
        )
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# SHARE CHAT
# =========================================================

@app.post(
    "/api/conversations/share/{conversation_id}"
)
def share_chat(
    conversation_id: str
):

    share_token = generate_token()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO shared_chats
        VALUES(?,?,?,?)
        """,
        (
            generate_id(),
            conversation_id,
            share_token,
            now()
        )
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "share_token": share_token
    }

# =========================================================
# VIEW SHARED CHAT
# =========================================================

@app.get("/api/shared/{share_token}")
def view_shared_chat(
    share_token: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM shared_chats
        WHERE share_token=?
        """,
        (share_token,)
    )

    shared = cur.fetchone()

    if not shared:
        conn.close()
        return {
            "success": False
        }

    cur.execute(
        """
        SELECT *
        FROM messages
        WHERE conversation_id=?
        ORDER BY created_at ASC
        """,
        (
            shared["conversation_id"],
        )
    )

    messages = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "messages": messages
    }

# =========================================================
# PART 2E COMPLETE
# NEXT:
# PART 2F
# TAGS + SEARCH INDEXING +
# CHAT ANALYTICS + SMART FILTERS
# =========================================================
# =========================================================
# PART 2F
# TAGS + SEARCH INDEXING + ANALYTICS
# PASTE BELOW PART 2E
# =========================================================

# =========================================================
# TABLES
# =========================================================

def create_tag_tables():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS conversation_tags(
        id TEXT PRIMARY KEY,
        conversation_id TEXT,
        tag TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_tag_tables()

# =========================================================
# REQUEST MODELS
# =========================================================

class AddTagRequest(BaseModel):
    conversation_id: str
    tag: str

class RemoveTagRequest(BaseModel):
    conversation_id: str
    tag: str

# =========================================================
# ADD TAG
# =========================================================

@app.post("/api/tags/add")
def add_tag(
    data: AddTagRequest
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO conversation_tags
        VALUES(?,?,?,?)
        """,
        (
            generate_id(),
            data.conversation_id,
            data.tag.lower(),
            now()
        )
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# REMOVE TAG
# =========================================================

@app.post("/api/tags/remove")
def remove_tag(
    data: RemoveTagRequest
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM conversation_tags
        WHERE conversation_id=?
        AND tag=?
        """,
        (
            data.conversation_id,
            data.tag.lower()
        )
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# LIST TAGS
# =========================================================

@app.get(
    "/api/tags/{conversation_id}"
)
def list_tags(
    conversation_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT tag
        FROM conversation_tags
        WHERE conversation_id=?
        ORDER BY tag ASC
        """,
        (conversation_id,)
    )

    tags = [
        row["tag"]
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "tags": tags
    }

# =========================================================
# SEARCH BY TAG
# =========================================================

@app.get(
    "/api/search/tag/{tag}"
)
def search_by_tag(
    tag: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT c.*
        FROM conversations c
        JOIN conversation_tags t
        ON c.id=t.conversation_id
        WHERE t.tag=?
        ORDER BY c.updated_at DESC
        """,
        (
            tag.lower(),
        )
    )

    rows = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "results": rows
    }

# =========================================================
# USER ANALYTICS
# =========================================================

@app.get(
    "/api/analytics/user/{user_id}"
)
def user_analytics(
    user_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT COUNT(*)
        FROM conversations
        WHERE user_id=?
        """,
        (user_id,)
    )

    conversations = (
        cur.fetchone()[0]
    )

    cur.execute(
        """
        SELECT COUNT(*)
        FROM messages
        WHERE user_id=?
        """,
        (user_id,)
    )

    messages = (
        cur.fetchone()[0]
    )

    conn.close()

    return {
        "success": True,
        "conversations":
            conversations,
        "messages":
            messages
    }

# =========================================================
# TOP ACTIVE CHATS
# =========================================================

@app.get(
    "/api/analytics/top-chats"
)
def top_chats():

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            conversation_id,
            COUNT(*) as total
        FROM messages
        GROUP BY conversation_id
        ORDER BY total DESC
        LIMIT 20
        """
    )

    rows = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "results": rows
    }

# =========================================================
# PART 2F COMPLETE
# NEXT:
# PART 2G
# CHAT MEMORY + PINNED MESSAGES +
# PROMPTS + SYSTEM INSTRUCTIONS
# =========================================================
# =========================================================
# PART 2G
# CHAT MEMORY + PINNED MESSAGES +
# PROMPTS + SYSTEM INSTRUCTIONS
# PASTE BELOW PART 2F
# =========================================================

# =========================================================
# TABLES
# =========================================================

def create_memory_tables():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS pinned_messages(
        id TEXT PRIMARY KEY,
        message_id TEXT,
        conversation_id TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS system_prompts(
        id TEXT PRIMARY KEY,
        conversation_id TEXT,
        prompt TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_memory_tables()

# =========================================================
# REQUEST MODELS
# =========================================================

class PinMessageRequest(BaseModel):
    message_id: str
    conversation_id: str

class SystemPromptRequest(BaseModel):
    conversation_id: str
    prompt: str

# =========================================================
# PIN MESSAGE
# =========================================================

@app.post("/api/messages/pin")
def pin_message(
    data: PinMessageRequest
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO pinned_messages
        VALUES(?,?,?,?)
        """,
        (
            generate_id(),
            data.message_id,
            data.conversation_id,
            now()
        )
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# UNPIN MESSAGE
# =========================================================

@app.delete(
    "/api/messages/unpin/{message_id}"
)
def unpin_message(
    message_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM pinned_messages
        WHERE message_id=?
        """,
        (message_id,)
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# LIST PINNED MESSAGES
# =========================================================

@app.get(
    "/api/messages/pinned/{conversation_id}"
)
def pinned_messages(
    conversation_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT m.*
        FROM messages m
        JOIN pinned_messages p
        ON m.id=p.message_id
        WHERE p.conversation_id=?
        ORDER BY p.created_at DESC
        """,
        (conversation_id,)
    )

    rows = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "messages": rows
    }

# =========================================================
# SAVE SYSTEM PROMPT
# =========================================================

@app.post(
    "/api/system-prompt/save"
)
def save_system_prompt(
    data: SystemPromptRequest
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM system_prompts
        WHERE conversation_id=?
        """,
        (
            data.conversation_id,
        )
    )

    existing = cur.fetchone()

    if existing:

        cur.execute(
            """
            UPDATE system_prompts
            SET prompt=?,
                updated_at=?
            WHERE conversation_id=?
            """,
            (
                data.prompt,
                now(),
                data.conversation_id
            )
        )

    else:

        cur.execute(
            """
            INSERT INTO system_prompts
            VALUES(?,?,?,?,?)
            """,
            (
                generate_id(),
                data.conversation_id,
                data.prompt,
                now(),
                now()
            )
        )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# GET SYSTEM PROMPT
# =========================================================

@app.get(
    "/api/system-prompt/{conversation_id}"
)
def get_system_prompt(
    conversation_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM system_prompts
        WHERE conversation_id=?
        """,
        (conversation_id,)
    )

    row = cur.fetchone()

    conn.close()

    return {
        "success": True,
        "prompt":
            row["prompt"]
            if row else ""
    }

# =========================================================
# MEMORY SUMMARY
# =========================================================

@app.get(
    "/api/chat/memory/{conversation_id}"
)
def chat_memory(
    conversation_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT COUNT(*)
        FROM messages
        WHERE conversation_id=?
        """,
        (conversation_id,)
    )

    total_messages = (
        cur.fetchone()[0]
    )

    conn.close()

    return {
        "success": True,
        "conversation_id":
            conversation_id,
        "messages":
            total_messages
    }

# =========================================================
# PART 2G COMPLETE
# NEXT:
# PART 3A
# FILE UPLOADS + ATTACHMENTS +
# IMAGE STORAGE + MEDIA SYSTEM
# =========================================================
# =========================================================
# PART 3A
# FILE UPLOADS + ATTACHMENTS + MEDIA SYSTEM
# PASTE BELOW PART 2G
# =========================================================

import os
import shutil

# =========================================================
# FASTAPI FILES
# =========================================================

from fastapi import UploadFile, File

# =========================================================
# UPLOAD DIRECTORY
# =========================================================

UPLOAD_DIR = "uploads"

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)

# =========================================================
# TABLES
# =========================================================

def create_media_tables():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS attachments(
        id TEXT PRIMARY KEY,
        user_id TEXT,
        conversation_id TEXT,
        filename TEXT,
        file_type TEXT,
        file_size INTEGER,
        file_path TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_media_tables()

# =========================================================
# FILE HELPERS
# =========================================================

def get_attachment(
    attachment_id
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM attachments
        WHERE id=?
        """,
        (attachment_id,)
    )

    row = cur.fetchone()

    conn.close()

    return row

# =========================================================
# UPLOAD FILE
# =========================================================

@app.post("/api/files/upload")
async def upload_file(
    user_id: str,
    conversation_id: str,
    file: UploadFile = File(...)
):

    attachment_id = generate_id()

    filename = (
        f"{attachment_id}_"
        f"{file.filename}"
    )

    filepath = os.path.join(
        UPLOAD_DIR,
        filename
    )

    with open(
        filepath,
        "wb"
    ) as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    file_size = (
        os.path.getsize(filepath)
    )

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO attachments
        VALUES(?,?,?,?,?,?,?,?)
        """,
        (
            attachment_id,
            user_id,
            conversation_id,
            file.filename,
            file.content_type,
            file_size,
            filepath,
            now()
        )
    )

    conn.commit()
    conn.close()

    create_audit_log(
        user_id,
        "file_uploaded"
    )

    return {
        "success": True,
        "attachment_id":
            attachment_id,
        "filename":
            file.filename,
        "size":
            file_size
    }

# =========================================================
# LIST ATTACHMENTS
# =========================================================

@app.get(
    "/api/files/{conversation_id}"
)
def list_attachments(
    conversation_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM attachments
        WHERE conversation_id=?
        ORDER BY created_at DESC
        """,
        (conversation_id,)
    )

    files = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "files": files
    }

# =========================================================
# ATTACHMENT DETAILS
# =========================================================

@app.get(
    "/api/file/{attachment_id}"
)
def file_details(
    attachment_id: str
):

    attachment = get_attachment(
        attachment_id
    )

    if not attachment:
        return {
            "success": False
        }

    return {
        "success": True,
        "file":
            dict(attachment)
    }

# =========================================================
# DELETE FILE
# =========================================================

@app.delete(
    "/api/file/delete/{attachment_id}"
)
def delete_file(
    attachment_id: str
):

    attachment = get_attachment(
        attachment_id
    )

    if not attachment:
        return {
            "success": False
        }

    try:

        if os.path.exists(
            attachment["file_path"]
        ):
            os.remove(
                attachment["file_path"]
            )

    except:
        pass

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM attachments
        WHERE id=?
        """,
        (attachment_id,)
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# STORAGE STATS
# =========================================================

@app.get(
    "/api/storage/stats"
)
def storage_stats():

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT COUNT(*)
        FROM attachments
        """
    )

    total_files = (
        cur.fetchone()[0]
    )

    cur.execute(
        """
        SELECT SUM(file_size)
        FROM attachments
        """
    )

    total_storage = (
        cur.fetchone()[0] or 0
    )

    conn.close()

    return {
        "success": True,
        "files":
            total_files,
        "storage_bytes":
            total_storage
    }

# =========================================================
# PART 3A COMPLETE
# NEXT:
# PART 3B
# IMAGE PROCESSING +
# AVATARS + PROFILE MEDIA +
# IMAGE GENERATION
# =========================================================
# =========================================================
# PART 3B
# IMAGE PROCESSING + AVATARS + PROFILE MEDIA
# PASTE BELOW PART 3A
# =========================================================

from PIL import Image

# =========================================================
# PROFILE MEDIA TABLE
# =========================================================

def create_profile_media_tables():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS profile_media(
        id TEXT PRIMARY KEY,
        user_id TEXT,
        avatar_path TEXT,
        banner_path TEXT,
        updated_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_profile_media_tables()

# =========================================================
# IMAGE DIRECTORY
# =========================================================

IMAGE_DIR = "uploads/images"

os.makedirs(
    IMAGE_DIR,
    exist_ok=True
)

# =========================================================
# RESIZE IMAGE
# =========================================================

def resize_image(
    filepath,
    width=512,
    height=512
):

    try:

        image = Image.open(
            filepath
        )

        image.thumbnail(
            (width, height)
        )

        image.save(
            filepath
        )

        return True

    except:
        return False

# =========================================================
# UPLOAD AVATAR
# =========================================================

@app.post(
    "/api/profile/avatar"
)
async def upload_avatar(
    user_id: str,
    file: UploadFile = File(...)
):

    media_id = generate_id()

    filename = (
        f"avatar_{media_id}.png"
    )

    filepath = os.path.join(
        IMAGE_DIR,
        filename
    )

    with open(
        filepath,
        "wb"
    ) as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    resize_image(
        filepath,
        512,
        512
    )

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT OR REPLACE
        INTO profile_media
        VALUES(?,?,?,?,?)
        """,
        (
            media_id,
            user_id,
            filepath,
            "",
            now()
        )
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "avatar": filepath
    }

# =========================================================
# UPLOAD BANNER
# =========================================================

@app.post(
    "/api/profile/banner"
)
async def upload_banner(
    user_id: str,
    file: UploadFile = File(...)
):

    filename = (
        f"banner_{generate_id()}.png"
    )

    filepath = os.path.join(
        IMAGE_DIR,
        filename
    )

    with open(
        filepath,
        "wb"
    ) as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    resize_image(
        filepath,
        1600,
        600
    )

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE profile_media
        SET banner_path=?,
            updated_at=?
        WHERE user_id=?
        """,
        (
            filepath,
            now(),
            user_id
        )
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "banner": filepath
    }

# =========================================================
# GET PROFILE MEDIA
# =========================================================

@app.get(
    "/api/profile/media/{user_id}"
)
def get_profile_media(
    user_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM profile_media
        WHERE user_id=?
        """,
        (user_id,)
    )

    row = cur.fetchone()

    conn.close()

    return {
        "success": True,
        "media":
            dict(row)
            if row else None
    }

# =========================================================
# DELETE AVATAR
# =========================================================

@app.delete(
    "/api/profile/avatar/{user_id}"
)
def delete_avatar(
    user_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE profile_media
        SET avatar_path=''
        WHERE user_id=?
        """,
        (user_id,)
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# PART 3B COMPLETE
# NEXT:
# PART 3C
# IMAGE GENERATION +
# OCR + FILE PREVIEWS +
# MEDIA ANALYTICS
# =========================================================
# =========================================================
# PART 3C
# IMAGE GENERATION + OCR + FILE PREVIEWS
# PASTE BELOW PART 3B
# =========================================================

import base64

# =========================================================
# OPTIONAL OCR
# =========================================================

try:

    import pytesseract

    OCR_ENABLED = True

except:

    OCR_ENABLED = False

# =========================================================
# MEDIA ANALYTICS TABLE
# =========================================================

def create_media_analytics_tables():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS media_analytics(
        id TEXT PRIMARY KEY,
        attachment_id TEXT,
        views INTEGER DEFAULT 0,
        downloads INTEGER DEFAULT 0,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_media_analytics_tables()

# =========================================================
# OCR IMAGE
# =========================================================

@app.get(
    "/api/media/ocr/{attachment_id}"
)
def image_ocr(
    attachment_id: str
):

    if not OCR_ENABLED:

        return {
            "success": False,
            "message":
            "OCR not installed"
        }

    attachment = get_attachment(
        attachment_id
    )

    if not attachment:
        return {
            "success": False
        }

    try:

        image = Image.open(
            attachment["file_path"]
        )

        text = (
            pytesseract.image_to_string(
                image
            )
        )

        return {
            "success": True,
            "text": text
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }

# =========================================================
# IMAGE PREVIEW
# =========================================================

@app.get(
    "/api/media/preview/{attachment_id}"
)
def media_preview(
    attachment_id: str
):

    attachment = get_attachment(
        attachment_id
    )

    if not attachment:
        return {
            "success": False
        }

    try:

        with open(
            attachment["file_path"],
            "rb"
        ) as f:

            encoded = (
                base64.b64encode(
                    f.read()
                ).decode()
            )

        return {
            "success": True,
            "filename":
                attachment["filename"],
            "preview":
                encoded
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }

# =========================================================
# TRACK VIEW
# =========================================================

@app.post(
    "/api/media/view/{attachment_id}"
)
def track_media_view(
    attachment_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM media_analytics
        WHERE attachment_id=?
        """,
        (attachment_id,)
    )

    row = cur.fetchone()

    if row:

        cur.execute(
            """
            UPDATE media_analytics
            SET views=views+1
            WHERE attachment_id=?
            """,
            (attachment_id,)
        )

    else:

        cur.execute(
            """
            INSERT INTO media_analytics
            VALUES(?,?,?,?,?)
            """,
            (
                generate_id(),
                attachment_id,
                1,
                0,
                now()
            )
        )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# TRACK DOWNLOAD
# =========================================================

@app.post(
    "/api/media/download/{attachment_id}"
)
def track_download(
    attachment_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE media_analytics
        SET downloads=downloads+1
        WHERE attachment_id=?
        """,
        (attachment_id,)
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# MEDIA STATS
# =========================================================

@app.get(
    "/api/media/stats/{attachment_id}"
)
def media_stats(
    attachment_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM media_analytics
        WHERE attachment_id=?
        """,
        (attachment_id,)
    )

    row = cur.fetchone()

    conn.close()

    return {
        "success": True,
        "stats":
            dict(row)
            if row else {
                "views": 0,
                "downloads": 0
            }
    }

# =========================================================
# PART 3C COMPLETE
# NEXT:
# PART 3D
# VIDEO SUPPORT +
# AUDIO SUPPORT +
# DOCUMENT PROCESSING
# =========================================================
# =========================================================
# PART 3D
# VIDEO SUPPORT + AUDIO SUPPORT +
# DOCUMENT PROCESSING
# PASTE BELOW PART 3C
# =========================================================

from fastapi.responses import FileResponse

# =========================================================
# MEDIA TABLES
# =========================================================

def create_document_tables():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS media_files(
        id TEXT PRIMARY KEY,
        attachment_id TEXT,
        media_type TEXT,
        duration REAL DEFAULT 0,
        pages INTEGER DEFAULT 0,
        metadata TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_document_tables()

# =========================================================
# SUPPORTED TYPES
# =========================================================

VIDEO_TYPES = [
    "video/mp4",
    "video/webm",
    "video/quicktime"
]

AUDIO_TYPES = [
    "audio/mpeg",
    "audio/wav",
    "audio/ogg"
]

DOCUMENT_TYPES = [
    "application/pdf",
    "text/plain"
]

# =========================================================
# REGISTER MEDIA FILE
# =========================================================

def register_media_file(
    attachment_id,
    media_type
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO media_files
        VALUES(?,?,?,?,?,?,?)
        """,
        (
            generate_id(),
            attachment_id,
            media_type,
            0,
            0,
            "{}",
            now()
        )
    )

    conn.commit()
    conn.close()

# =========================================================
# ANALYZE FILE TYPE
# =========================================================

@app.post(
    "/api/media/analyze/{attachment_id}"
)
def analyze_media(
    attachment_id: str
):

    attachment = get_attachment(
        attachment_id
    )

    if not attachment:
        return {
            "success": False
        }

    file_type = (
        attachment["file_type"]
    )

    if file_type in VIDEO_TYPES:

        media_type = "video"

    elif file_type in AUDIO_TYPES:

        media_type = "audio"

    elif file_type in DOCUMENT_TYPES:

        media_type = "document"

    else:

        media_type = "unknown"

    register_media_file(
        attachment_id,
        media_type
    )

    return {
        "success": True,
        "media_type":
            media_type
    }

# =========================================================
# STREAM MEDIA
# =========================================================

@app.get(
    "/api/media/stream/{attachment_id}"
)
def stream_media(
    attachment_id: str
):

    attachment = get_attachment(
        attachment_id
    )

    if not attachment:
        return {
            "success": False
        }

    return FileResponse(
        attachment["file_path"]
    )

# =========================================================
# DOCUMENT TEXT EXTRACTION
# =========================================================

@app.get(
    "/api/document/text/{attachment_id}"
)
def document_text(
    attachment_id: str
):

    attachment = get_attachment(
        attachment_id
    )

    if not attachment:
        return {
            "success": False
        }

    try:

        if (
            attachment["file_type"]
            == "text/plain"
        ):

            with open(
                attachment["file_path"],
                "r",
                encoding="utf-8"
            ) as f:

                text = f.read()

            return {
                "success": True,
                "text": text
            }

        return {
            "success": False,
            "message":
            "Unsupported document"
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }

# =========================================================
# DOCUMENT METADATA
# =========================================================

@app.get(
    "/api/document/meta/{attachment_id}"
)
def document_metadata(
    attachment_id: str
):

    attachment = get_attachment(
        attachment_id
    )

    if not attachment:
        return {
            "success": False
        }

    return {
        "success": True,
        "filename":
            attachment["filename"],
        "type":
            attachment["file_type"],
        "size":
            attachment["file_size"]
    }

# =========================================================
# LIST MEDIA FILES
# =========================================================

@app.get("/api/media/list")
def list_media():

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM media_files
        ORDER BY created_at DESC
        """
    )

    rows = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "media": rows
    }

# =========================================================
# PART 3D COMPLETE
# NEXT:
# PART 3E
# PDF PROCESSING +
# TRANSCRIPTIONS +
# THUMBNAILS +
# MEDIA SEARCH
# =========================================================
# =========================================================
# PART 3D
# VIDEO SUPPORT + AUDIO SUPPORT +
# DOCUMENT PROCESSING
# PASTE BELOW PART 3C
# =========================================================

from fastapi.responses import FileResponse

# =========================================================
# MEDIA TABLES
# =========================================================

def create_document_tables():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS media_files(
        id TEXT PRIMARY KEY,
        attachment_id TEXT,
        media_type TEXT,
        duration REAL DEFAULT 0,
        pages INTEGER DEFAULT 0,
        metadata TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_document_tables()

# =========================================================
# SUPPORTED TYPES
# =========================================================

VIDEO_TYPES = [
    "video/mp4",
    "video/webm",
    "video/quicktime"
]

AUDIO_TYPES = [
    "audio/mpeg",
    "audio/wav",
    "audio/ogg"
]

DOCUMENT_TYPES = [
    "application/pdf",
    "text/plain"
]

# =========================================================
# REGISTER MEDIA FILE
# =========================================================

def register_media_file(
    attachment_id,
    media_type
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO media_files
        VALUES(?,?,?,?,?,?,?)
        """,
        (
            generate_id(),
            attachment_id,
            media_type,
            0,
            0,
            "{}",
            now()
        )
    )

    conn.commit()
    conn.close()

# =========================================================
# ANALYZE FILE TYPE
# =========================================================

@app.post(
    "/api/media/analyze/{attachment_id}"
)
def analyze_media(
    attachment_id: str
):

    attachment = get_attachment(
        attachment_id
    )

    if not attachment:
        return {
            "success": False
        }

    file_type = (
        attachment["file_type"]
    )

    if file_type in VIDEO_TYPES:

        media_type = "video"

    elif file_type in AUDIO_TYPES:

        media_type = "audio"

    elif file_type in DOCUMENT_TYPES:

        media_type = "document"

    else:

        media_type = "unknown"

    register_media_file(
        attachment_id,
        media_type
    )

    return {
        "success": True,
        "media_type":
            media_type
    }

# =========================================================
# STREAM MEDIA
# =========================================================

@app.get(
    "/api/media/stream/{attachment_id}"
)
def stream_media(
    attachment_id: str
):

    attachment = get_attachment(
        attachment_id
    )

    if not attachment:
        return {
            "success": False
        }

    return FileResponse(
        attachment["file_path"]
    )

# =========================================================
# DOCUMENT TEXT EXTRACTION
# =========================================================

@app.get(
    "/api/document/text/{attachment_id}"
)
def document_text(
    attachment_id: str
):

    attachment = get_attachment(
        attachment_id
    )

    if not attachment:
        return {
            "success": False
        }

    try:

        if (
            attachment["file_type"]
            == "text/plain"
        ):

            with open(
                attachment["file_path"],
                "r",
                encoding="utf-8"
            ) as f:

                text = f.read()

            return {
                "success": True,
                "text": text
            }

        return {
            "success": False,
            "message":
            "Unsupported document"
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }

# =========================================================
# DOCUMENT METADATA
# =========================================================

@app.get(
    "/api/document/meta/{attachment_id}"
)
def document_metadata(
    attachment_id: str
):

    attachment = get_attachment(
        attachment_id
    )

    if not attachment:
        return {
            "success": False
        }

    return {
        "success": True,
        "filename":
            attachment["filename"],
        "type":
            attachment["file_type"],
        "size":
            attachment["file_size"]
    }

# =========================================================
# LIST MEDIA FILES
# =========================================================

@app.get("/api/media/list")
def list_media():

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM media_files
        ORDER BY created_at DESC
        """
    )

    rows = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "media": rows
    }

# =========================================================
# PART 3D COMPLETE
# NEXT:
# PART 3E
# PDF PROCESSING +
# TRANSCRIPTIONS +
# THUMBNAILS +
# MEDIA SEARCH
# =========================================================
# =========================================================
# PART 3E
# API KEYS + PROVIDER MANAGEMENT
# PASTE BELOW PART 3D
# =========================================================

class SaveProviderKeyRequest(BaseModel):
    user_id: str
    provider: str
    api_key: str

def create_provider_tables():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS provider_keys(
        id TEXT PRIMARY KEY,
        user_id TEXT,
        provider TEXT,
        api_key TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_provider_tables()

@app.post("/api/providers/save-key")
def save_provider_key(
    data: SaveProviderKeyRequest
):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT id
    FROM provider_keys
    WHERE user_id=?
    AND provider=?
    """, (
        data.user_id,
        data.provider
    ))

    existing = cur.fetchone()

    if existing:
        cur.execute("""
        UPDATE provider_keys
        SET api_key=?,
            updated_at=?
        WHERE id=?
        """, (
            data.api_key,
            now(),
            existing["id"]
        ))
    else:
        cur.execute("""
        INSERT INTO provider_keys
        VALUES(?,?,?,?,?,?)
        """, (
            generate_id(),
            data.user_id,
            data.provider,
            data.api_key,
            now(),
            now()
        ))

    conn.commit()
    conn.close()

    return {
        "success": True
    }

@app.get("/api/providers/{user_id}")
def list_provider_keys(
    user_id: str
):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT
        provider,
        created_at,
        updated_at
    FROM provider_keys
    WHERE user_id=?
    ORDER BY provider ASC
    """, (user_id,))

    rows = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "providers": rows
    }

@app.delete(
    "/api/providers/delete/{user_id}/{provider}"
)
def delete_provider_key(
    user_id: str,
    provider: str
):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    DELETE FROM provider_keys
    WHERE user_id=?
    AND provider=?
    """, (
        user_id,
        provider
    ))

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# PART 3E COMPLETE
# NEXT:
# PART 3F = MULTI-PROVIDER ROUTING +
# FAILOVER + MODEL PRIORITIES
# =========================================================
export interface ProviderConfig {
  id: string;
  enabled: boolean;
  priority: number;
  timeoutMs: number;
  models: string[];
}

export const PROVIDERS: ProviderConfig[] = [
  {
    id: "openai",
    enabled: true,
    priority: 1,
    timeoutMs: 30000,
    models: [
      "gpt-5.5",
      "gpt-5",
      "gpt-4o"
    ]
  },
  {
    id: "anthropic",
    enabled: true,
    priority: 2,
    timeoutMs: 30000,
    models: [
      "claude-opus",
      "claude-sonnet"
    ]
  },
  {
    id: "google",
    enabled: true,
    priority: 3,
    timeoutMs: 30000,
    models: [
      "gemini-pro",
      "gemini-flash"
    ]
  }
];
export interface ProviderHealth {
  status: "healthy" | "degraded" | "offline";
  successCount: number;
  failureCount: number;
  lastSuccess?: number;
  lastFailure?: number;
}

export const providerHealth =
  new Map<string, ProviderHealth>();
export function markSuccess(id: string) {
  const existing =
    providerHealth.get(id);

  providerHealth.set(id, {
    status: "healthy",
    successCount:
      (existing?.successCount ?? 0) + 1,
    failureCount:
      existing?.failureCount ?? 0,
    lastSuccess: Date.now(),
    lastFailure: existing?.lastFailure
  });
}

export function markFailure(id: string) {
  const existing =
    providerHealth.get(id);

  const failures =
    (existing?.failureCount ?? 0) + 1;

  providerHealth.set(id, {
    status:
      failures >= 5
        ? "offline"
        : "degraded",
    successCount:
      existing?.successCount ?? 0,
    failureCount: failures,
    lastSuccess: existing?.lastSuccess,
    lastFailure: Date.now()
  });
}
export async function routeRequest(
  model?: string
) {
  const available =
    PROVIDERS
      .filter(p => p.enabled)
      .sort(
        (a, b) =>
          a.priority - b.priority
      );

  if (!model) {
    return available;
  }

  const match = available.find(
    provider =>
      provider.models.some(
        m =>
          model
            .toLowerCase()
            .includes(
              m.toLowerCase()
            )
      )
  );

  return match
    ? [match]
    : available;
}
export async function withTimeout(
  promise: Promise<any>,
  timeoutMs: number
) {
  return Promise.race([
    promise,
    new Promise((_, reject) =>
      setTimeout(
        () =>
          reject(
            new Error(
              "Provider timeout"
            )
          ),
        timeoutMs
      )
    )
  ]);
}
export async function executeWithFailover(
  providers,
  requestFn
) {
  let lastError;

  for (const provider of providers) {
    try {
      const result =
        await withTimeout(
          requestFn(provider),
          provider.timeoutMs
        );

      markSuccess(provider.id);

      return result;
    } catch (error) {
      markFailure(provider.id);

      console.error(
        `[FAILOVER] ${provider.id}`,
        error
      );

      lastError = error;
    }
  }

  throw lastError;
}
export function logProviderEvent(
  provider: string,
  event: string,
  metadata?: Record<string, any>
) {
  console.log(
    JSON.stringify({
      timestamp:
        new Date().toISOString(),
      provider,
      event,
      metadata
    })
  );
}
export async function runInference(
  model: string,
  request: any
) {
  const providers =
    await routeRequest(model);

  return executeWithFailover(
    providers,
    async provider => {
      logProviderEvent(
        provider.id,
        "request_started"
      );

      const response =
        await providerClient(
          provider.id
        ).chat(request);

      logProviderEvent(
        provider.id,
        "request_completed"
      );

      return response;
    }
  );
}
export interface UsageRecord {
  userId: string;
  workspaceId: string;
  providerId: string;
  model: string;

  promptTokens: number;
  completionTokens: number;
  totalTokens: number;

  estimatedCost: number;
  createdAt: Date;
}
export async function recordUsage(
  usage: UsageRecord
) {
  return db.usage.create({
    data: usage
  })
export function estimateCost(
  promptTokens: number,
  completionTokens: number,
  pricing: ModelPricing
) {
  return (
    promptTokens *
      pricing.inputPrice +
    completionTokens *
      pricing.outputPrice
  );
}
export interface RequestPolicy {
  maxRequestsPerMinute: number;
  maxConcurrentRequests: number;
}
export async function checkLimits(
  userId: string
) {
  const usage =
    await getRecentUsage(userId);

  if (usage > LIMITS.maxRequestsPerMinute) {
    throw new Error(
      "Rate limit exceeded"
    );
  }
}
export interface WorkspaceBudget {
  workspaceId: string;
  monthlyBudget: number;
  currentSpend: number;
}
export interface ProviderBudget {
  providerId: string;
  monthlyLimit: number;
  currentSpend: number;
}
 Request flooding
• Token spikes
• Infinite retry loops
• Prompt spam
• Excessive concurrency
• Suspicious API usage
• Total requests
• Total tokens
• Cost per provider
• Cost per model
• Cost per workspace
• Daily usage trends
• Monthly usage trends
export interface CacheEntry<T> {
  key: string;
  value: T;
  createdAt: Date;
  expiresAt: Date;
}
export async function getCachedResponse(
  key: string
) {
  return cache.get(key);
}

export async function setCachedResponse(
  key: string,
  value: unknown,
  ttl: number
) {
  return cache.set(
    key,
    value,
    ttl
  );
}
import crypto from "crypto";

export function buildCacheKey(
  model: string,
  prompt: string
) {
  return crypto
    .createHash("sha256")
    .update(`${model}:${prompt}`)
    .digest("hex");
}
import crypto from "crypto";

export function buildCacheKey(
  model: string,
  prompt: string
) {
  return crypto
    .createHash("sha256")
    .update(`${model}:${prompt}`)
    .digest("hex");
}
export async function executeRequest(
  model: string,
  prompt: string
) {
  const key =
    buildCacheKey(
      model,
      prompt
    );

  const cached =
    await getCachedResponse(key);

  if (cached) {
    return cached;
  }

  const result =
    await runInference(
      model,
      prompt
    );

  await setCachedResponse(
    key,
    result,
    3600
  );

  return result;
}
• Model lists
• Pricing tables
• Provider health
• Routing rules
• Capabilities
export async function invalidateCache(
  key: string
) {
  await cache.delete(key);
}
• Cache hits
• Cache misses
• Hit ratio
• Average latency
• Saved provider calls
• Saved cost
• Response caching
• Metadata caching
• Connection pooling
• Request deduplication
• Parallel provider checks
• Warm cache loading
export interface LogEvent {
  level:
    | "info"
    | "warn"
    | "error";

  service: string;
  event: string;
  timestamp: Date;

  metadata?: Record<
    string,
    unknown
  >;
}
export function logEvent(
  event: LogEvent
) {
  console.log(
    JSON.stringify(event)
  );
}
• Total requests
• Successful requests
• Failed requests
• Provider usage
• Model usage
• Average latency
• P95 latency
• P99 latency
export interface ProviderMetrics {
  providerId: string;

  successRate: number;
  errorRate: number;

  avgLatency: number;
  requests: number;
}
export function captureError(
  error: Error,
  context?: object
) {
  logEvent({
    level: "error",
    service: "gateway",
    event: error.message,
    metadata: context,
    timestamp: new Date()
  });
}
• Provider outage
• High latency
• Increased error rate
• Failover activation
• Budget threshold reached
• Database connectivity issues
• System status
• Provider status
• Active requests
• Request volume
• Error rates
• Latency metrics
• Budget consumption
• Model changes
• Routing updates
• Provider additions
• Provider removals
• Permission changes
• Administrative actions
export interface ProviderSecret {
  providerId: string;
  encryptedKey: string;
  createdAt: Date;
}
export async function getProviderKey(
  providerId: string
) {
  return secrets.get(
    providerId
  );
}
export interface AuthToken {
  userId: string;
  issuedAt: Date;
  expiresAt: Date;
}
export type Role =
  | "owner"
  | "admin"
  | "member"
  | "service";
export interface Permission {
  resource: string;
  action: string;
}
export interface ProviderPolicy {
  providerId: string;
  enabled: boolean;
  allowedModels: string[];
}
• Required fields
• Model existence
• Provider availability
• Input size limits
• Request schema
• API keys
• User credentials
• Internal tokens
• Sensitive configuration
• Audit records
• Login events
• Failed authentication
• Permission changes
• Secret rotation
• Provider access attempts
• Administrative actions
• PostgreSQL
• Redis
• Object Storage
• Audit Storage
export interface ProviderRecord {
  id: string;
  name: string;

  enabled: boolean;

  createdAt: Date;
  updatedAt: Date;
}
export interface ModelRecord {
  id: string;

  providerId: string;
  model: string;

  enabled: boolean;
}
export interface RoutingConfig {
  model: string;

  providers: string[];

  failoverEnabled: boolean;
}
export interface UsageRecord {
  id: string;

  providerId: string;
  model: string;

  promptTokens: number;
  completionTokens: number;

  cost: number;

  createdAt: Date;
}
export interface AuditRecord {
  id: string;

  actor: string;
  action: string;

  timestamp: Date;
}
• Cache entries
• Provider health
• Routing state
• Rate limits
• Active requests
export interface Repository<T> {
  create(data: T): Promise<T>;

  update(
    id: string,
    data: Partial<T>
  ): Promise<T>;

  delete(
    id: string
  ): Promise<void>;

  findById(
    id: string
  ): Promise<T | null>;
}
GET    /admin/providers
POST   /admin/providers
PATCH  /admin/providers/:id
DELETE /admin/providers/:id
GET    /admin/models
POST   /admin/models
PATCH  /admin/models/:id
DELETE /admin/models/:id
GET   /admin/routing
PATCH /admin/routing
{
  model: "gpt-5",
  providers: [
    "openai",
    "anthropic",
    "google"
  ]
}
GET /admin/health/providers
GET /admin/health/system
{
  provider: "openai",
  status: "healthy",
  latency: 412
}
GET /admin/usage
GET /admin/usage/providers
GET /admin/usage/models
GET /admin/audit
{
  actor: "admin",
  action: "provider_disabled",
  timestamp: Date.now()
}
POST /admin/cache/clear

POST /admin/cache/rebuild
export interface FeatureFlag {
  key: string;

  enabled: boolean;
}
export class RequestQueue {
  private running = 0;
  private queue: Array<() => Promise<void>> =
    [];

  constructor(
    private maxConcurrent = 10
  ) {}

  async add(
    task: () => Promise<void>
  ) {
    this.queue.push(task);
    this.process();
  }

  private async process() {
    if (
      this.running >=
        this.maxConcurrent ||
      this.queue.length === 0
    ) {
      return;
    }

    const task =
      this.queue.shift();

    if (!task) return;

    this.running++;

    try {
      await task();
    } finally {
      this.running--;
      this.process();
    }
  }
}
export interface RetryPolicy {
  maxAttempts: number;
  initialDelayMs: number;
  maxDelayMs: number;
}
export function calculateDelay(
  attempt: number,
  baseDelay: number
) {
  return (
    baseDelay *
    Math.pow(2, attempt)
  );
}
export async function retry(
  fn: () => Promise<any>,
  policy: RetryPolicy
) {
  let attempt = 0;

  while (
    attempt <
    policy.maxAttempts
  ) {
    try {
      return await fn();
    } catch (error) {
      attempt++;

      if (
        attempt >=
        policy.maxAttempts
      ) {
        throw error;
      }

      await new Promise(
        resolve =>
          setTimeout(
            resolve,
            calculateDelay(
              attempt,
              policy.initialDelayMs
            )
          )
      );
    }
  }
}
• Network timeout
• Temporary provider outage
• Rate-limit response
• Connection reset
• Gateway timeout
• Invalid request
• Authentication failure
• Permission denied
• Unsupported model
• Validation error
export interface CircuitBreaker {
  providerId: string;
  failureCount: number;
  open: boolean;
}
• Retry count
• Recovery rate
• Provider failures
• Circuit breaker events
• Failover activations
• Provider adapters
• Routing engine
• Failover logic
• Retry engine
• Cache layer
• Budget controls
• Database connectivity
• Redis connectivity
• Provider APIs
• Secret retrieval
• End-to-end inference flow
• Provider outage handling
• Automatic failover
• Retry recovery
• Circuit breaker activation
• Concurrent requests
• Queue performance
• Latency under load
• Throughput limits
• Authentication
• Authorization
• Secret access
• Request validation
• Input sanitization
GET /health

{
  status: "healthy",
  database: "healthy",
  cache: "healthy",
  providers: "healthy"
}
✓ Environment variables loaded
✓ Database migrations applied
✓ Redis connected
✓ Secrets accessible
✓ Providers reachable
✓ Monitoring enabled
✓ Alerts configured
• All tests passing
• No critical vulnerabilities
• Failover validated
• Monitoring active
• Audit logging enabled
• Backups configured
✓ Unit tests
✓ Integration tests
✓ Failover testing
✓ Load testing
✓ Security validation
✓ Health checks
✓ Deployment validation
✓ Production readiness checklist
• Unified inference endpoint
• Request validation
• Model abstraction
• Provider abstraction
• Streaming support
• Versioned APIs
• SSE streaming
• WebSocket support
• Token streaming
• Realtime events
• Connection management
• TypeScript SDK
• Python SDK
• Go SDK
• Java SDK
• Request helpers
• Authentication helpers
• API key creation
• Key rotation
• Key revocation
• Access scopes
• Rate limiting
• Developer authentication
• Request analytics
• Token analytics
• Cost analytics
• Provider analytics
• Error analytics
• Exportable reports
• API documentation
• SDK documentation
• Quick-start guides
• Code examples
• Changelog
• Developer dashboard
✓ Unified AI Gateway
✓ Streaming support
✓ Multi-language SDKs
✓ API key management
✓ Analytics platform
✓ Developer portal
✓ Documentation system
✓ External developer ecosystem
• Tenant isolation
• Workspace management
• Tenant quotas
• Tenant-level routing
• Tenant configuration
• Usage aggregation
• Cost attribution
• Department budgets
• Cost reports
• Invoice generation
• SSO
• SAML/OAuth
• Audit retention
• Compliance controls
• Data governance
• Horizontal scaling
• Multi-region deployment
• Load balancing
• Autoscaling
• Global traffic routing
• Backup strategy
• Recovery procedures
• Cross-region replication
• Failover testing
• Incident recovery
• Incident management
• On-call workflows
• Capacity planning
• SLA monitoring
• Reliability engineering
✓ Multi-tenant platform
✓ Enterprise governance
✓ Cost allocation system
✓ Global infrastructure
✓ Disaster recovery
✓ SRE operations framework
✓ Enterprise-grade scalability
✓ Production maturity



