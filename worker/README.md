# Cloud Agent

This package is the only application component intended for Azure deployment. It has two processes that use the same image:

- `worker.app.api` accepts authenticated jobs and exposes job status.
- Celery consumes jobs from Redis and generates study packages.

Neither process connects to the application's PostgreSQL or SQLite database.

Agent API:

```bash
uvicorn worker.app.api:app --host 0.0.0.0 --port 8010
```

Background worker:

```bash
celery -A worker.app.celery_app:celery_app worker --loglevel=info
```

Required cloud configuration:

```env
REDIS_URL=rediss://...
AGENT_API_KEY=use-a-strong-secret
AGENT_RESULT_EXPIRES_SECONDS=604800
LLM_BASE_URL=
LLM_API_KEY=
OPENAI_API_KEY=
```

An empty `LLM_BASE_URL` uses the deterministic generator. The OpenAI URL selects the paid agent; another OpenAI-compatible URL selects the free-compatible agent.
