# ShopHub — Async FastAPI Marketplace

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://docker.com)
[![Stripe](https://img.shields.io/badge/Payments-Stripe-635BFF?logo=stripe)](https://stripe.com)

A full-featured e-commerce marketplace built with a microservice architecture. Users can register, browse and filter products, manage a shopping cart, pay via Stripe, leave reviews, and track orders in real time via WebSocket. Admins manage products and categories through the Swagger UI.

---

## Features

- **JWT Authentication** — access + refresh token pair, role-based access (admin / regular user)
- **Product catalog** — full-text search, price range filter, in-stock filter, pagination, Redis cache (60 s TTL)
- **Shopping cart** — add / remove items, live quantity control, order summary
- **Stripe Checkout** — hosted payment page, webhook confirms order and closes cart
- **Real-time orders** — WebSocket endpoint (`/ws/orders`) pushes order status updates to the client
- **Product reviews** — star rating + comment, one review per user per product, average rating
- **Image uploads** — multipart upload stored on Cloudflare R2 (S3-compatible)
- **Email notifications** — account-verification email sent asynchronously via RabbitMQ consumer
- **Server-rendered UI** — Jinja2 templates with Bootstrap, no separate SPA build step
- **Automated migrations** — Alembic runs `upgrade head` on every container start
- **API docs** — Swagger UI at `/api/docs`, ReDoc at `/api/redoc`
- **Project docs** — MkDocs Material at port 8100

---

## Architecture

```
Browser
  │
  ▼
Nginx :80
  ├─ /api/*  ──────────────────►  backend_api (FastAPI :9999)
  │                                    │          │         │
  │                                 Postgres   Redis   Cloudflare R2
  │                                    │
  │                              RabbitMQ (CloudAMQP)
  │                                    │
  │                             notification_service
  │                              (email consumer)
  │
  └─ /*  ──────────────────────►  frontend (FastAPI/Jinja2 :12345)
                                       │
                                 proxies to backend_api
```

| Container | Stack | Role |
|---|---|---|
| `backend_api` | FastAPI · SQLAlchemy 2 (async) · Alembic · Pydantic v2 | REST API |
| `frontend` | FastAPI · Jinja2 · Bootstrap 5 | Server-rendered UI |
| `notification` | pika (RabbitMQ consumer) | Transactional emails |
| `redis` | Redis 7 | Product-list cache |
| `nginx_2_project1` | Nginx alpine | Reverse proxy |
| `documentation` | MkDocs Material | Dev docs at :8100 |

**External services:** Neon (serverless Postgres) · Cloudflare R2 · CloudAMQP (RabbitMQ) · Stripe

---

## Tech Stack

| Layer | Technologies |
|---|---|
| Language | Python 3.12 |
| API framework | FastAPI, Pydantic v2 |
| ORM / DB | SQLAlchemy 2 (async), Alembic, PostgreSQL |
| Auth | JWT (PyJWT), bcrypt, OAuth2 password flow |
| Caching | Redis (`redis.asyncio`), prefix-based cache invalidation |
| Storage | Cloudflare R2 via `aioboto3` |
| Payments | Stripe SDK, webhook signature verification |
| Messaging | RabbitMQ (CloudAMQP) via `pika` |
| Real-time | WebSocket with per-user connection manager |
| Frontend | Jinja2, Bootstrap 5, vanilla JS (fetch API) |
| Email | `smtplib` / SMTP SSL, HTML + plain-text multipart |
| DevOps | Docker Compose, Nginx, Makefile |
| Code quality | black, isort, flake8 |

---

## Getting Started

### Prerequisites
- Docker & Docker Compose

### 1. Clone & configure

```bash
git clone <repo-url>
cd fastapi_marketplace
cp .env-example .env
# Fill in the values (see section below)
```

### 2. Environment variables (`.env`)

| Variable | Description |
|---|---|
| `DATABASE_URL` | Async Postgres DSN (`postgresql+asyncpg://...`) |
| `JWT_SECRET` | Secret for signing JWT tokens |
| `STRIPE_SECRET_KEY` | Stripe API key |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret (optional) |
| `STRIPE_SUCCESS_URL` | Redirect after successful payment |
| `STRIPE_CANCEL_URL` | Redirect after cancelled payment |
| `AWS_ACCESS_KEY_ID` | R2 / S3 access key |
| `AWS_SECRET_ACCESS_KEY` | R2 / S3 secret key |
| `AWS_S3_BUCKET_NAME` | Bucket name |
| `AWS_S3_ENDPOINT_URL` | R2 endpoint URL |
| `AWS_S3_BASE_URL` | Public base URL for images |
| `RMQ_HOST` | RabbitMQ hostname |
| `RMQ_PORT` | RabbitMQ port (usually 5671 for TLS) |
| `RMQ_USER` | RabbitMQ username |
| `RMQ_PASSWORD` | RabbitMQ password |
| `RMQ_VIRTUAL_HOST` | RabbitMQ virtual host |
| `SMTP_SERVER` | SMTP server hostname |
| `USER` | SMTP sender address |
| `TOKEN_UKR_NET` | SMTP password / app token |

### 3. Run

```bash
docker compose up --build
```

Alembic migrations run automatically on backend startup.

| URL | Description |
|---|---|
| http://localhost | Web UI |
| http://localhost:9999/api/docs | Swagger UI |
| http://localhost:9999/api/redoc | ReDoc |
| http://localhost:8100 | Project documentation |

### Handy commands

```bash
make up      # docker compose up -d
make down    # docker compose down
make bash    # shell into backend container
```

---

## API Reference

### Auth

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/auth/login` | — | Login → `{access_token, refresh_token}` |
| `POST` | `/api/auth/refresh` | — | Refresh → new token pair |
| `GET` | `/api/auth/get-my-info` | JWT | Current user profile |

### Users

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/users/create` | — | Register (sends verification email) |
| `GET` | `/api/users/verify/{uuid}` | — | Activate account from email link |

### Products & Categories

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/products/` | — | List products with filters & pagination |
| `GET` | `/api/products/{pk}` | — | Product details |
| `POST` | `/api/products/` | admin | Create product (multipart image upload) |
| `DELETE` | `/api/products/{pk}` | admin | Delete product + invalidate cache |
| `GET` | `/api/categories/` | — | List categories |
| `POST` | `/api/categories/` | admin | Create category |
| `DELETE` | `/api/categories/{pk}` | admin | Delete category |

**Product filter query params:** `q`, `page`, `category_id`, `min_price`, `max_price`, `in_stock`

### Cart

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/carts/` | JWT | Current cart |
| `PATCH` | `/api/carts/change-products` | JWT | Add / remove quantity |

### Reviews

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/reviews/product/{id}` | — | Reviews + average rating |
| `POST` | `/api/reviews/product/{id}` | JWT | Submit review (one per user) |
| `DELETE` | `/api/reviews/{id}` | JWT | Delete own review |

### Payments & Orders

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/payment/payment-stripe-data` | JWT | Create Stripe Checkout session → `{url, order_id}` |
| `POST` | `/api/payment/webhook` | Stripe | Mark order paid (webhook) |
| `GET` | `/api/orders/` | JWT | User's order history |
| `GET` | `/api/orders/{id}` | JWT | Order details |

### WebSocket

| Endpoint | Auth | Description |
|---|---|---|
| `ws://host/ws/orders?token=<jwt>` | JWT (query param) | Real-time order status updates |

---

## Checkout Flow

```
1. GET /api/payment/payment-stripe-data
      → creates Stripe Checkout session
      → saves Order{status: PENDING} in DB
      → returns { url, order_id }

2. User pays on Stripe-hosted page

3. Stripe POST /api/payment/webhook
      → verifies signature
      → marks Order{status: PAID}
      → WebSocket pushes update to user
```

---

## Project Layout

```
fastapi_marketplace/
├── backend_api/
│   └── app/
│       ├── applications/
│       │   ├── auth/         # JWT handler, security deps
│       │   ├── products/     # Products, categories, cart (router · crud · schemas · models)
│       │   ├── orders/       # Order creation & retrieval
│       │   ├── payment/      # Stripe integration & webhook
│       │   ├── reviews/      # Product reviews
│       │   ├── users/        # Registration & verification
│       │   └── ws/           # WebSocket order updates
│       ├── database/         # Async session factory
│       ├── migrations/       # Alembic versions
│       └── services/
│           ├── rabbit/       # RabbitMQ publisher
│           ├── redis/        # Cache helpers
│           ├── s3/           # R2 upload wrapper
│           └── websocket/    # Connection manager
│
├── frontend/
│   └── app/
│       ├── backend_api/      # httpx API client
│       ├── routers/          # Page routes + frontend proxy routes
│       ├── templates/        # Jinja2 HTML templates
│       └── static/           # CSS / JS
│
├── notification_service/
│   └── app/
│       └── main.py           # RabbitMQ consumer → SMTP email sender
│
├── nginx/
│   └── nginx.conf
├── documentation/            # MkDocs Material source
├── docker-compose.yml
├── Makefile
└── .env-example
```

---

## Code Quality

```bash
black --line-length 120 backend_api/app frontend/app notification_service/app
isort --profile black --line-length 120 backend_api/app frontend/app notification_service/app
flake8 backend_api/app frontend/app notification_service/app
```
