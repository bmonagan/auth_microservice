# schemas.py
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional
import re


# ─────────────────────────────────────────
# AUTH SCHEMAS
# ─────────────────────────────────────────

class RegisterSchema(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class RefreshSchema(BaseModel):
    refresh_token: str


class LogoutSchema(BaseModel):
    refresh_token: str


# ─────────────────────────────────────────
# TOKEN SCHEMAS (responses)
# ─────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ─────────────────────────────────────────
# USER SCHEMAS
# ─────────────────────────────────────────

class UserPublic(BaseModel):
    id: int
    email: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}  # replaces orm_mode in Pydantic v2


class UserInDB(UserPublic):
    hashed_password: str  # never returned to client, used internally


class UpdateProfileSchema(BaseModel):
    email: EmailStr


class ChangePasswordSchema(BaseModel):
    old_password: str
    new_password: str


class DeleteAccountSchema(BaseModel):
    password: str


# ─────────────────────────────────────────
# SESSION SCHEMAS (multi-device)
# ─────────────────────────────────────────

class SessionInfo(BaseModel):
    id: int
    device_info: Optional[str]
    created_at: datetime
    expires_at: datetime

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    sessions: list[SessionInfo]


# ─────────────────────────────────────────
# ERROR SCHEMAS
# ─────────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str