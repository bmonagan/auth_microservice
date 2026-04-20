#!/usr/bin/env bash
set -euo pipefail

# Sensible local defaults; can be overridden by exported env vars.
export SECRET_KEY="${SECRET_KEY:-dev-secret-key-change-me}"
export ALGORITHM="${ALGORITHM:-HS256}"
export ACCESS_TOKEN_EXPIRE_MINUTES="${ACCESS_TOKEN_EXPIRE_MINUTES:-15}"
export REFRESH_TOKEN_EXPIRE_DAYS="${REFRESH_TOKEN_EXPIRE_DAYS:-7}"
export DATABASE_URL="${DATABASE_URL:-sqlite:///./dev.db}"

# Ensure DB tables exist before serving requests.
uv run python -c "from src.database import Base, engine; import src.models; Base.metadata.create_all(bind=engine)"

echo "Starting FastAPI on http://127.0.0.1:${PORT:-8000}"
exec uv run uvicorn src.main:app --reload --host "${HOST:-127.0.0.1}" --port "${PORT:-8000}"
