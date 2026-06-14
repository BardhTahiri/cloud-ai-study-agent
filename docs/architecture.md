# Architecture

Initial architecture target:

```text
Student Browser
    ↓
Frontend
    ↓
Backend API
    ↓
Queue
    ↓
Cloud AI Worker
    ↓
Database + Storage + AI Provider
```

The backend should create tasks quickly, while the worker handles longer AI operations in the background.

## Current MVP

```text
React Frontend
    ↓
FastAPI Backend
    ↓
Local Worker Function
    ↓
In-Memory Store
```

The current implementation runs the worker synchronously so the first demo is easy to run. The task model already includes status, progress, and results, which makes it ready to move to a real queue later.
