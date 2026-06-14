# Database

The MVP uses SQLite by default:

```text
storage/cloud_ai_study_agent.db
```

The database stores the persistent state that proves the agent is cloud-ready:

- courses
- uploaded/pasted study material
- study task status
- generated summaries
- generated quizzes
- generated study plans
- worker errors, if a task fails

## Tables

```text
courses
study_tasks
```

`study_tasks.result` stores the generated package as JSON. This keeps the MVP simple while preserving the full output from the worker.

## Migration

The first schema is documented in:

```text
database/migrations/0001_initial_schema.sql
```

The application currently creates tables automatically at startup through SQLAlchemy. Later, this can be replaced with Alembic migrations.

## PostgreSQL

Docker Compose includes a PostgreSQL service:

```text
postgres:16-alpine
```

When the app is started with Docker Compose, the backend uses:

```text
DATABASE_URL=postgresql://study_agent:study_agent_password@postgres:5432/cloud_ai_study_agent
```

To run only PostgreSQL in Docker and run the backend locally, start:

```bash
docker compose up postgres
```

Then set:

```text
DATABASE_URL=postgresql://study_agent:study_agent_password@localhost:5432/cloud_ai_study_agent
```
