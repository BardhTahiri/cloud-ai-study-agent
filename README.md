# Cloud AI Study Agent

Cloud-based AI study assistant that processes academic materials and generates:

- summaries
- quizzes
- study plans
- important topics

The current version uses a hybrid cloud-agent workflow:

- `frontend`, `backend`, uploaded files, and the permanent database remain local.
- the local backend sends extracted material to an authenticated cloud agent API.
- Redis carries temporary cloud jobs and results.
- a Celery worker generates the study package without access to the local database.
- the local backend copies completed results into its local database.

## Planned Structure

```text
cloud-ai-study-agent/
+-- frontend/          # Student web interface
+-- backend/           # API, auth, courses, documents, tasks
+-- worker/            # Cloud AI agent/background processor
+-- database/          # Migrations and seed data
+-- docs/              # Architecture, thesis notes, demo flow
+-- infra/             # Docker and cloud deployment files
+-- scripts/           # Developer/helper scripts
+-- storage/           # Local development uploads and SQLite DB
```

## Core Workflow

```text
Student uploads PDF or enters prompt
|
v
Backend creates a processing task
|
v
Local backend sends extracted text to the cloud agent
|
v
Cloud worker analyzes the content
|
v
System generates summary, quiz, and study plan
|
v
Results return to the local database and student dashboard
```

## Run Locally

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cd ..
uvicorn backend.app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Then open:

```text
http://localhost:5173
```

## Run With The Azure Agent

Set `TASK_QUEUE_MODE=cloud`, `AGENT_BASE_URL`, and `AGENT_API_KEY` in the ignored `.env` file, then start the local application:

```bash
docker compose up --build
```

Only PostgreSQL, the backend, and the frontend start locally. The backend sends study jobs to the configured Azure agent API.

## Simulate The Agent Locally

The Redis, agent API, and Celery worker services are available through the optional `local-agent` profile:

```powershell
$env:TASK_QUEUE_MODE="cloud"
$env:AGENT_BASE_URL="http://agent-api:8010"
$env:AGENT_API_KEY="local-agent-key"
docker compose --profile local-agent up --build
```

Backend health should show the active database:

```text
http://localhost:8000/health
```

In this profile, the backend submits a remote-style job to the local `agent-api`. The Celery worker processes it independently, and frontend polling copies the completed result into PostgreSQL.

## Select The Study Agent

The implementation is selected from `LLM_BASE_URL`. The other model settings can remain configured while you switch the URL.

Offline generator, with no API cost or model server:

```env
LLM_BASE_URL=
```

Free/local OpenAI-compatible model, such as Ollama running on the Docker host:

```env
LLM_BASE_URL=http://host.docker.internal:11434/v1
FREE_LLM_MODEL=qwen3:8b
LLM_API_KEY=
FREE_LLM_MAX_INPUT_CHARS=12000
```

For an OpenAI-compatible cloud endpoint, use that provider's `/v1` URL, free model name, and API key in the same variables. Free-provider input is condensed to `FREE_LLM_MAX_INPUT_CHARS` before submission so large PDFs do not exceed token-per-minute limits.

ChatGPT subscription through Codex:

```env
LLM_BASE_URL=codex://subscription
CODEX_MODEL=gpt-5.6-sol
CODEX_TIMEOUT_SECONDS=300
LLM_MAX_INPUT_CHARS=100000
```

Codex is not exposed as an HTTP API like Groq. The worker image runs the official Codex CLI in read-only, ephemeral mode and validates its final response against the same strict JSON Schema used by Groq. It removes API-key variables before starting Codex, so this mode must use the ChatGPT login cached under `CODEX_HOME` and consumes the account's Codex allowance.

For the local agent profile, build the image, sign in once, and verify the cached session:

```powershell
docker compose --profile local-agent up --build -d
docker compose --profile local-agent exec worker codex login --device-auth
docker compose --profile local-agent exec worker codex login status
```

The `codex_auth` Docker volume persists refreshed credentials. Treat that volume like a password. The Azure worker uses the same design with a private Azure Files mount at `/codex-auth`.

Configured providers do not silently fall back to offline output. In cloud mode, temporary provider failures are retried every `AGENT_PROVIDER_RETRY_DELAY_SECONDS` for up to `AGENT_PROVIDER_MAX_RETRIES` attempts; the defaults are five minutes and 288 retries, or about 24 hours. Set `LLM_FALLBACK_TO_OFFLINE=true` only when deterministic fallback is explicitly desired. Azure continues processing while the local computer is off. The result remains in Redis for `AGENT_RESULT_EXPIRES_SECONDS` (seven days by default), and the backend copies it into PostgreSQL when the app is opened again.

## MVP Features

- create/select a course
- paste academic material or upload a PDF/text file
- submit a prompt
- generate important topics
- generate a summary
- generate quiz questions
- generate a multi-day study plan
- view recent study tasks
- persist courses and tasks in SQLite
- poll task status while background processing finishes
- process remote agent jobs through an authenticated API, Redis, and Celery
- switch between free-compatible and ChatGPT-authenticated Codex agents

## Next Implementation Steps

- add authentication
- add RAG/vector search for uploaded materials
- deploy only the agent API and worker as Azure Container Apps
