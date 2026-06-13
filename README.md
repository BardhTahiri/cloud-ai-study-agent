# Cloud AI Study Agent

Cloud-based AI study assistant that will process academic materials and generate:

- summaries
- quizzes
- study plans
- important topics

The first version of this repository contains only the project skeleton.

## Planned Structure

```text
cloud-ai-study-agent/
├── frontend/          # Student web interface
├── backend/           # API, auth, courses, documents, tasks
├── worker/            # Cloud AI agent/background processor
├── database/          # Migrations and seed data
├── docs/              # Architecture, thesis notes, demo flow
├── infra/             # Docker and cloud deployment files
├── scripts/           # Developer/helper scripts
└── storage/           # Local development uploads only
```

## Core Workflow

```text
Student uploads PDF or enters prompt
↓
Backend creates a processing task
↓
Cloud AI worker extracts and analyzes the content
↓
System generates summary, quiz, and study plan
↓
Results are saved and shown in the student dashboard
```
