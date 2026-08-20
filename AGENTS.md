# Repository Guidelines

## Project Structure & Module Organization

`backend/app/` contains the FastAPI application, API routes, schemas, services, and SQLAlchemy database code. Backend tests live in `backend/tests/`. `worker/app/` contains the cloud agent API, Celery configuration, LLM agents, and study-package processors; its tests are in `worker/tests/`. The React and TypeScript interface is under `frontend/src/`. Database migrations belong in `database/migrations/`, Azure deployment notes and diagrams in `infra/azure/`, and broader design documentation in `docs/`. Uploaded files are written beneath `storage/uploads/` and must not be committed.

## Architecture & Configuration

The default setup is hybrid: the frontend, backend, PostgreSQL database, and uploaded materials run locally, while Azure hosts the agent API, Celery worker, and Redis queue. Copy `.env.example` to `.env` for local configuration. Never commit `.env`, database passwords, Redis URLs, or LLM/API keys. Configure production credentials as Azure Container Apps secrets.

## Build, Test, and Development Commands

- `python -m pip install -r backend/requirements-dev.txt` installs backend, worker, and test dependencies.
- `uvicorn backend.app.main:app --reload` starts the local API.
- From `frontend/`, run `npm install` and `npm run dev` to start Vite.
- From `frontend/`, run `npm run build` to type-check and build the UI.
- `docker compose up --build` starts the default hybrid stack.
- `docker compose --profile local-agent up --build` also runs the agent services locally.
- `python -m pytest -q` runs all Python tests.

## Coding Style & Naming Conventions

Use four-space indentation and type hints in Python. Name modules and functions with `snake_case`, and classes and Pydantic models with `PascalCase`. In TypeScript, use two-space indentation, `PascalCase` for React components and types, and `camelCase` for variables and functions. Preserve surrounding style; no repository-wide formatter or linter is currently configured.

## Testing Guidelines

Pytest discovers `test_*.py` files under `backend/tests/` and `worker/tests/`. Add focused tests for API behavior, task state transitions, provider responses, and failure recovery. Run a targeted directory while iterating, then run the full suite before opening a pull request. No formal coverage threshold is enforced.

## Commit & Pull Request Guidelines

History uses short, action-oriented subjects such as `Adding database configuration`. Prefer imperative wording, for example `Add cloud task recovery`, and keep each commit focused. Pull requests should explain behavior changes, identify configuration or migration steps, link related issues, list tests run, and include screenshots for visible frontend changes.
