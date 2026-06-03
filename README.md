# ph.lab.subscriptionportal

Base scaffold for a SaaS platform to manage courses and subscriptions.

Architecture: FastAPI (backend) + Vue 3 (frontend) + SQL Server + Alembic migrations.

Quick start (using Docker):

1. Copy `.env` and set secrets.
2. Build and start:

```bash
docker compose up --build
```

Run migrations (inside backend container):

```bash
docker compose exec backend bash
# inside container
alembic revision --autogenerate -m "initial migration"
alembic upgrade head
```

Notes:
- Full code-first approach: models are defined with SQLAlchemy and Alembic autogenerate reads `app.models.Base.metadata`.
- JWT authentication, repository and service patterns are scaffolded.
- Prepared for async evolution and microservices split.
