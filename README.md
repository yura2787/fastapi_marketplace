# FastAPI Marketplace

A microservice-based marketplace built with **FastAPI**. Users can register, browse
products, manage a shopping cart and pay via **Stripe**. The project is split into
independent services orchestrated with **Docker Compose**.

## Architecture

| Service | Stack | Description |
|---|---|---|
| `backend_api` | FastAPI, SQLAlchemy (async), Alembic, PostgreSQL | REST API: auth, users, products, cart, payments |
| `frontend` | FastAPI, Jinja2, Bootstrap | Server-rendered web UI that talks to the API |
| `notification_service` | RabbitMQ consumer | Sends transactional emails (e.g. account verification) |
| `nginx` | Nginx | Reverse proxy: `/` → frontend, `/api/` → backend |
| `local_database` | PostgreSQL 16 | Primary data store |
| `documentation` | MkDocs Material | Project docs |

External services: **Stripe** (payments), **S3-compatible storage** (product images,
e.g. Cloudflare R2), **RabbitMQ** (CloudAMQP), **Sentry** (error tracking).

## Tech stack

Python 3.12 · FastAPI · SQLAlchemy 2 (async) · Alembic · PostgreSQL · Pydantic v2 ·
JWT auth · Stripe · RabbitMQ · Docker · Nginx · Poetry

## Getting started

### 1. Prerequisites
- Docker & Docker Compose

### 2. Configure environment
```bash
cp .env-example .env
```
Then fill in the real values in `.env` (Postgres, `JWT_SECRET`, Stripe, S3, RabbitMQ).

### 3. Run
```bash
docker compose up --build
```

The stack will be available at:

| URL | Service |
|---|---|
| http://localhost/ | Web UI (via Nginx) |
| http://localhost:9999/api/docs | API Swagger docs |
| http://localhost:8100 | Project documentation |

Database migrations run automatically on backend start (`alembic upgrade head`).

### Handy commands
```bash
make up      # docker compose up
make down    # docker compose down
make bash    # shell into the backend container
```

## API overview

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/users/create` | — | Register a new user |
| POST | `/api/auth/login` | — | Login, returns access + refresh tokens |
| POST | `/api/auth/refresh` | — | Exchange a refresh token for a new pair |
| GET | `/api/auth/get-my-info` | ✅ | Current user info |
| GET | `/api/products/` | — | List products (search + pagination) |
| GET | `/api/products/{pk}` | — | Product details |
| POST | `/api/products/` | admin | Create a product (with image upload) |
| GET | `/api/carts/` | ✅ | Current user's cart |
| PATCH | `/api/carts/change-products` | ✅ | Add/remove items from cart |
| GET | `/api/payment/payment-stripe-data` | ✅ | Create a Stripe checkout session |

## Code quality

Formatting and linting run in CI on every pull request:
```bash
black --line-length 120 backend_api/app frontend/app notification_service/app
isort --profile black --line-length 120 backend_api/app frontend/app notification_service/app
flake8 backend_api/app frontend/app notification_service/app
```

## Project layout
```
backend_api/          FastAPI REST API
frontend/             Jinja2 web UI
notification_service/ RabbitMQ email consumer
nginx/                Reverse proxy config
documentation/        MkDocs site
docker-compose.yml    Service orchestration
```
