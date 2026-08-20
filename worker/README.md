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
AGENT_PROVIDER_RETRY_DELAY_SECONDS=300
AGENT_PROVIDER_MAX_RETRIES=288
LLM_BASE_URL=
LLM_API_KEY=
FREE_LLM_MAX_INPUT_CHARS=12000
CODEX_MODEL=gpt-5.6-sol
CODEX_BIN=codex
CODEX_HOME=/codex-auth
CODEX_TIMEOUT_SECONDS=300
LLM_FALLBACK_TO_OFFLINE=false
```

An empty `LLM_BASE_URL` uses the deterministic generator. `codex://subscription` selects the ChatGPT-authenticated Codex CLI, while an HTTP OpenAI-compatible URL selects the free-compatible agent. Free-provider material is condensed to `FREE_LLM_MAX_INPUT_CHARS` before the request.

With a provider selected and offline fallback disabled, temporary provider failures are rescheduled through Celery every five minutes for about 24 hours by default. A retry remains in the `processing` state, releases the worker between attempts, and survives local application shutdown because the queue runs in Azure. Completed results remain in Redis for the configured result-retention period.

Codex runs with `--ephemeral`, a read-only sandbox, ignored user rules, and a strict output schema. Academic material is piped over stdin instead of being written to disk. The child receives only a small allowlist of operating-system variables, so Redis credentials, provider keys, and other worker secrets are not exposed and subscription mode cannot silently use API billing.

`CODEX_HOME` must be writable and persistent because Codex refreshes `auth.json` in place. For local Docker, the `codex_auth` volume is mounted there. Authenticate with:

```powershell
docker compose --profile local-agent exec worker codex login --device-auth
docker compose --profile local-agent exec worker codex login status
```

Use this provider only for a private demonstration. Do not expose a personal Codex session as a general public execution service.
