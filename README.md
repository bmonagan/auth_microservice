## Live Testing (One Command)

Start the API with auto-reload and auto-create local SQLite tables:

```bash
./scripts/dev.sh
```

Then open:

- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/openapi.json
- http://127.0.0.1:8000/health/live
- http://127.0.0.1:8000/health

### Optional overrides

You can override host/port and env values when running:

```bash
HOST=0.0.0.0 PORT=9000 DATABASE_URL=sqlite:///./local.db ./scripts/dev.sh
```

## Docker Setup

Build and start the API + Redis:

```bash
docker compose up --build
```

Then open:

- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/openapi.json

Run in detached mode:

```bash
docker compose up --build -d
```

Stop containers:

```bash
docker compose down
```

Use a custom secret key (recommended):

```bash
SECRET_KEY="your-strong-secret" docker compose up --build
```

## Docker Production Profile (PostgreSQL)

This project includes a production-oriented Compose override that switches the app database to PostgreSQL and keeps Redis internal-only.

Prepare environment file:

```bash
cp .env.prod.example .env.prod
```

Start production stack:

```bash
docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

Stop production stack:

```bash
docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml down
```

Notes:

- Update SECRET_KEY and POSTGRES_PASSWORD in .env.prod before deploying.
- PostgreSQL data is persisted in the postgres_data Docker volume.
- The base docker-compose.yml remains a local development stack using SQLite.
- Docker marks the app container healthy only when /health/ready returns 200.
