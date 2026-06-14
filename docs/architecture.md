# Architecture

Final architecture target:

```text
Student Browser
    |
    v
Frontend
    |
    v
Backend API
    |
    v
Queue
    |
    v
Cloud AI Worker
    |
    v
Database + Storage + AI Provider
```

The backend should create tasks quickly, while the worker handles longer AI operations in the background.

## Current MVP

```text
React Frontend
    |
    v
FastAPI Backend
    |
    v
Background Task
    |
    v
Local Study Agent
    |
    v
SQLite Database
```

The current implementation persists courses and study tasks in SQLite by default. Task creation returns quickly with a pending task, then FastAPI background tasks run the local study agent and store the completed result.

This keeps the workflow close to the final cloud version while staying simple to run locally. The next infrastructure upgrade is replacing FastAPI background tasks with Redis/Celery or another cloud queue.
