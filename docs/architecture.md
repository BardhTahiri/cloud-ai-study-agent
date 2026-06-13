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
