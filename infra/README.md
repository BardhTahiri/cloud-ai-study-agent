# Infrastructure

Deployment and cloud configuration files will live here.

Planned areas:

- Docker
- Azure deployment
- environment configuration
- CI/CD notes

## Current Database Setup

Local development uses SQLite through:

```text
DATABASE_URL=sqlite:///./storage/cloud_ai_study_agent.db
```

For cloud deployment, the same backend can point to PostgreSQL by changing `DATABASE_URL`.

Example:

```text
DATABASE_URL=postgresql://user:password@host:5432/cloud_ai_study_agent
```

## Docker PostgreSQL

The default `docker-compose.yml` now includes:

- `postgres` for PostgreSQL 16
- `backend` connected to PostgreSQL through `DATABASE_URL`
- `frontend` connected to the backend API

Run the full stack:

```bash
docker compose up --build
```

Run only the database:

```bash
docker compose up postgres
```

Default development credentials:

```text
POSTGRES_DB=cloud_ai_study_agent
POSTGRES_USER=study_agent
POSTGRES_PASSWORD=study_agent_password
```

The backend creates the current tables automatically at startup. The schema is also documented in:

```text
database/migrations/0001_initial_schema.sql
```
