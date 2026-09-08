# BIMVORA API — FastAPI Backend

Python 3.12 · FastAPI · SQLAlchemy 2.0 async · PostgreSQL · Alembic

## Quick Start (local dev)

```bash
# 1. Create virtualenv
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env — set DATABASE_URL to your local PostgreSQL

# 4. Start the server (migrations run automatically on startup)
uvicorn app.main:app --reload --port 8000

# API available at: http://localhost:8000
# Swagger docs at:  http://localhost:8000/docs  (DEBUG=true only)
```

## Key Architecture Note — MissingGreenlet Fix

This backend uses **two separate SQLAlchemy engines**:

| Context | Driver | URL format |
|---|---|---|
| FastAPI app | `asyncpg` (async) | `postgresql+asyncpg://...` |
| Alembic migrations | `psycopg2` (sync) | `postgresql+psycopg2://...` |

The `settings.sync_database_url` property in `app/config.py` automatically
converts the `DATABASE_URL` env var from asyncpg to psycopg2 for Alembic.

This prevents the `sqlalchemy.exc.MissingGreenlet` error that occurs when
`await_only()` is called in a synchronous context.

## EasyPanel Deployment

1. Create a new service → From GitHub
2. Set build method: **Dockerfile**
3. Set port: **8000**
4. Set domain: **api.bimvora.com** with SSL
5. Add all environment variables from `.env.example`
6. Set `DATABASE_URL` using EasyPanel's internal PostgreSQL hostname

Migrations run automatically on every container start.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check + DB connectivity |
| GET | `/products` | List products (with filters) |
| GET | `/products/{slug}` | Product detail |
| GET | `/categories` | All categories with children |
| GET | `/categories/{slug}` | Single category |
| POST | `/orders` | Create order + Stripe PI |
| GET | `/orders/{id}/status` | Order status |
| POST | `/webhooks/stripe` | Stripe webhook handler |
| POST | `/tracking/event` | Server-side CAPI events |
| GET | `/downloads/{token}` | Resolve download token → signed URL |
| POST | `/newsletter/subscribe` | Newsletter subscription |
