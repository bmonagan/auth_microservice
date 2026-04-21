from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from src.auth.email import send_verification_email, send_password_reset_email
from src.auth.hashing import hash_password, verify_password
from src.auth.jwt import (
    create_access_token,
    create_email_verification_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
)
from src.database import get_db
from src.limiter import limiter
from src.models import RefreshToken, User
from src.schemas import LoginSchema, RegisterSchema, ForgotPasswordSchema, ResetPasswordSchema

router = APIRouter()


@router.post("/register", status_code=201)
def register(payload: RegisterSchema, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        is_active=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    verification_token = create_email_verification_token(user.id, user.email)
    send_verification_email(user.email, verification_token)

    return {
        "message": "User created. Check your email to verify your account.",
        "user_id": user.id,
    }


@router.get("/verify-email")
def verify_email(token: str = Query(...), db: Session = Depends(get_db)):
    payload = decode_token(token)
    if not payload or payload.get("type") != "email_verification":
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")

    user_id = payload.get("sub")
    token_email = payload.get("email")
    if not user_id or not token_email:
        raise HTTPException(status_code=400, detail="Invalid verification payload")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.email != token_email:
        raise HTTPException(status_code=400, detail="Verification link does not match current email")

    if user.is_active:
        return {"message": "Email already verified"}

    user.is_active = True
    db.commit()

    return {"message": "Email verified successfully"}


@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, payload: LoginSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Email not verified")

    access_token = create_access_token(user.id)
    refresh_token_str = create_refresh_token(user.id)

    token_record = RefreshToken(
        token=refresh_token_str,
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(token_record)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer",
    }


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    
    # Always return success to prevent email enumeration attacks
    if not user:
        return {"message": "If email exists, a password reset link has been sent"}
    
    reset_token = create_password_reset_token(user.id, user.email)
    send_password_reset_email(user.email, reset_token)
    
    return {"message": "If email exists, a password reset link has been sent"}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordSchema, db: Session = Depends(get_db)):
    decoded = decode_token(payload.token)
    if not decoded or decoded.get("type") != "password_reset":
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")

    user_id = decoded.get("sub")
    token_email = decoded.get("email")
    if not user_id or not token_email:
        raise HTTPException(status_code=400, detail="Invalid reset payload")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.email != token_email:
        raise HTTPException(status_code=400, detail="Reset link does not match current email")

    user.hashed_password = hash_password(payload.new_password)
    db.commit()

    return {"message": "Password reset successfully"}