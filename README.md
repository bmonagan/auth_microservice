## Live Testing (One Command)

Start the API with auto-reload and auto-create local SQLite tables:

```bash
./scripts/dev.sh
```

Then open:

- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/openapi.json

### Optional overrides

You can override host/port and env values when running:

```bash
HOST=0.0.0.0 PORT=9000 DATABASE_URL=sqlite:///./local.db ./scripts/dev.sh
```
