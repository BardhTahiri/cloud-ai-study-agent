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

## Simulate The Hybrid Stack

Docker Compose starts the local application and a local simulation of the cloud agent:

```bash
docker compose up --build
```

Backend health should show the active database:

```text
http://localhost:8000/health
```

The backend submits a remote-style job to `agent-api`. The Celery worker processes it independently, and frontend polling copies the completed result into PostgreSQL.

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
```

For an OpenAI-compatible cloud endpoint, use that provider's `/v1` URL, free model name, and API key in the same variables.

Paid OpenAI agent:

```env
LLM_BASE_URL=https://api.openai.com/v1
PAID_LLM_MODEL=gpt-5.6-sol
OPENAI_API_KEY=your_key_here
```

By default, a provider error falls back to the offline generator and records that fact in the result. Set `LLM_FALLBACK_TO_OFFLINE=false` when a provider error should fail the task instead.

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
- switch between free and paid model agents using the endpoint URL

## Next Implementation Steps

- add authentication
- add RAG/vector search for uploaded materials
- deploy only the agent API and worker as Azure Container Apps
