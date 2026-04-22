FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen

COPY src ./src

EXPOSE 8000

CMD ["sh", "-c", "uv run python -c \"from src.database import Base, engine; import src.models; Base.metadata.create_all(bind=engine)\" && uv run uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
