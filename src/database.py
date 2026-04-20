# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,        # drops stale connections before using them
    pool_size=10,              # max persistent connections in pool
    max_overflow=20,           # extra connections allowed under load
    echo=False                 # set True to log all SQL (useful for debugging)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

# FastAPI dependency — used in every route that needs DB access
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()