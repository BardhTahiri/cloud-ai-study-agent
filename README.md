# Cloud AI Study Agent

Cloud-based AI study assistant that processes academic materials and generates:

- summaries
- quizzes
- study plans
- important topics

The current version is a local MVP that keeps the cloud-agent structure visible:

- `backend` exposes the API and creates study tasks.
- `worker` acts as the first AI agent/background processor.
- `frontend` gives the student a dashboard for generating outputs.
- generated results are stored in a local SQLite database by default.

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
Background study agent extracts and analyzes the content
|
v
System generates summary, quiz, and study plan
|
v
Results are saved and shown in the student dashboard
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

## Next Implementation Steps

- add Redis/Celery queue for real background jobs
- move the SQLite database URL to PostgreSQL for cloud deployment
- add authentication
- connect the worker to an LLM provider
- add RAG/vector search for uploaded materials
- deploy backend and worker as cloud containers
