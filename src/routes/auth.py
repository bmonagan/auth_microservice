
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.schemas import RegisterSchema
from src.routes.users import User
from src.database import get_db
from src.auth.hashing import hash_password

router = APIRouter()

@router.post("/register", status_code=201)
def register(payload: RegisterSchema, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User created", "user_id": user.id}