# main.py
from fastapi import FastAPI
from slowapi import Limiter
from slowapi.util import get_remote_address
from src.routes import auth, users

limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter

app.include_router(auth.router, prefix="/auth")
app.include_router(users.router)  # already has /users prefix