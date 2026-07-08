# backend_api

FastAPI REST API for the marketplace — authentication, users, products, cart and
Stripe payments. Uses async SQLAlchemy with PostgreSQL and Alembic migrations.

Runs as the `backend_api` service in the root `docker-compose.yml`.
See the [root README](../README.md) for the full setup.

## Structure
```
app/
├── app_factory.py        FastAPI app + router wiring
├── main.py               ASGI entrypoint
├── settings.py           Pydantic settings (env-driven)
├── database/             Async engine & session
├── migrations/           Alembic migrations
├── applications/
│   ├── auth/             Login, JWT, current-user dependency
│   ├── users/            Registration, verification
│   ├── products/         Products & cart
│   └── payment/          Stripe checkout
└── services/
    ├── s3/               Product image uploads
    └── rabbit/           RabbitMQ publisher
```

## Local dev
```bash
poetry install
alembic upgrade head
uvicorn main:app --reload --port 9999
```

Swagger docs: http://localhost:9999/api/docs
