# main.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text

from src.cache import get_redis_client
from src.database import engine
from src.limiter import limiter
from src.routes import auth, users

app = FastAPI()
app.state.limiter = limiter

app.include_router(auth.router, prefix="/auth")
app.include_router(users.router)  # already has /users prefix


def _check_database() -> bool:
	try:
		with engine.connect() as connection:
			connection.execute(text("SELECT 1"))
		return True
	except Exception:
		return False


def _check_redis() -> bool:
	try:
		client = get_redis_client()
		if not client:
			return False
		return bool(client.ping())
	except Exception:
		return False


@app.get("/health/live")
def health_live():
	return {"status": "alive"}


@app.get("/health")
def health():
	db_ok = _check_database()
	redis_ok = _check_redis()
	checks = {
		"database": "ok" if db_ok else "error",
		"redis": "ok" if redis_ok else "error",
	}

	if db_ok:
		return {"status": "ok", "checks": checks}
	return JSONResponse(status_code=503, content={"status": "unhealthy", "checks": checks})


@app.get("/health/ready")
def health_ready():
	db_ok = _check_database()
	redis_ok = _check_redis()
	checks = {
		"database": "ok" if db_ok else "error",
		"redis": "ok" if redis_ok else "error",
	}

	if db_ok and redis_ok:
		return {"status": "ok", "checks": checks}
	return JSONResponse(status_code=503, content={"status": "unhealthy", "checks": checks})