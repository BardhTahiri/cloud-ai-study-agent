# Infrastructure

The deployment uses a hybrid architecture:

- frontend, backend, uploads, and the permanent database remain local
- Azure Container Registry stores the cloud agent image
- Azure Container Apps runs the agent API and Celery worker
- Azure Managed Redis carries jobs and stores temporary results

PostgreSQL is not required in Azure for this architecture.

## Docker Simulation

`docker-compose.yml` runs the same split locally:

- `backend`, `frontend`, and `postgres` represent the local application
- `agent-api`, `worker`, and `redis` represent the cloud agent

```bash
docker compose up --build
```

The local backend calls `http://agent-api:8010`, while only the agent worker has the LLM configuration.

See `infra/azure/README.md` for the Azure deployment sequence.
