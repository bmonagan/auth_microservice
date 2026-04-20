# routes/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from src.auth.dependencies import get_current_user
from src.auth.hashing import hash_password, verify_password
from src.database import get_db
from src.models import RefreshToken, User
from src.schemas import (
    ChangePasswordSchema,
    DeleteAccountSchema,
    SessionInfo,
    SessionListResponse,
    UpdateProfileSchema,
    UserPublic,
)

router = APIRouter(prefix="/users", tags=["users"])


# ─────────────────────────────────────────
# GET /users/me
# ─────────────────────────────────────────

@router.get("/me", response_model=UserPublic)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return current_user


# ─────────────────────────────────────────
# PATCH /users/me
# ─────────────────────────────────────────

@router.patch("/me", response_model=UserPublic)
def update_me(
    payload: UpdateProfileSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update email. Triggers re-verification if email changes."""
    if payload.email and payload.email != current_user.email:
        existing = db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = payload.email
        current_user.is_active = False  # force re-verification

    db.commit()
    db.refresh(current_user)
    return current_user


# ─────────────────────────────────────────
# POST /users/me/change-password
# ─────────────────────────────────────────

@router.post("/me/change-password", status_code=204)
def change_password(
    payload: ChangePasswordSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify old password, hash and store new one, revoke all sessions."""
    if not verify_password(payload.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    if payload.old_password == payload.new_password:
        raise HTTPException(status_code=400, detail="New password must differ from old")

    current_user.hashed_password = hash_password(payload.new_password)

    # Security: revoke all refresh tokens on password change
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id
    ).update({"revoked": True})

    db.commit()


# ─────────────────────────────────────────
# DELETE /users/me
# ─────────────────────────────────────────

@router.delete("/me", status_code=204)
def delete_account(
    payload: DeleteAccountSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Require password confirmation before hard delete."""
    if not verify_password(payload.password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")

    db.delete(current_user)  # cascade deletes refresh tokens
    db.commit()


# ─────────────────────────────────────────
# GET /users/me/sessions
# ─────────────────────────────────────────

@router.get("/me/sessions", response_model=SessionListResponse)
def get_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return all active sessions for the current user."""
    sessions = db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.revoked == False,
        RefreshToken.expires_at > datetime.now(timezone.utc)
    ).all()

    return {"sessions": sessions}


# ─────────────────────────────────────────
# DELETE /users/me/sessions/{session_id}
# ─────────────────────────────────────────

@router.delete("/me/sessions/{session_id}", status_code=204)
def revoke_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke a specific session by ID (remote logout)."""
    session = db.query(RefreshToken).filter(
        RefreshToken.id == session_id,
        RefreshToken.user_id == current_user.id  # ownership check — critical
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.revoked = True
    db.commit()


# ─────────────────────────────────────────
# DELETE /users/me/sessions
# ─────────────────────────────────────────

@router.delete("/me/sessions", status_code=204)
def revoke_all_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke all sessions — 'log out everywhere' button."""
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id
    ).update({"revoked": True})

    db.commit()