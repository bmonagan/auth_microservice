# models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database import Base

class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True)
    email           = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    refresh_tokens  = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id          = Column(Integer, primary_key=True)
    token       = Column(String, unique=True, nullable=False, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at  = Column(DateTime(timezone=True), nullable=False)
    revoked     = Column(Boolean, default=False)
    device_info = Column(String, nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    user        = relationship("User", back_populates="refresh_tokens")