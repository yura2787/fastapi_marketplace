# frontend

Server-rendered web UI for the marketplace, built with FastAPI + Jinja2 templates and
Bootstrap. It calls the `backend_api` over HTTP and stores the access token in an
httpOnly cookie.

Runs as the `frontend` service in the root `docker-compose.yml`.
See the [root README](../README.md) for the full setup.

## Structure
```
app/
├── app_factory.py        FastAPI app + static mount
├── main.py               ASGI entrypoint
├── settings.py           Pydantic settings
├── backend_api/api.py    HTTP client for the backend
├── routers/              Page routes (index, login, register, product)
├── templates/            Jinja2 templates
└── static/               CSS / assets
```

## Local dev
```bash
poetry install
uvicorn main:app --reload --port 12345
```

Requires `BACKEND_API` to point at the running API (e.g. `http://localhost:9999/api/`).
