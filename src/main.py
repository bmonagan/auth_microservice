# main.py
from fastapi import FastAPI
from src.limiter import limiter
from src.routes import auth, users

app = FastAPI()
app.state.limiter = limiter

app.include_router(auth.router, prefix="/auth")
app.include_router(users.router)  # already has /users prefix