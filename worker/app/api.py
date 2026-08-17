from __future__ import annotations

from hmac import compare_digest
from typing import Annotated, Any, Literal

from celery import states
from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field, ValidationError

from worker.app.agents.contracts import StudyInput, StudyOutput
from worker.app.celery_app import celery_app
from worker.app.config import settings
from worker.app.jobs.study_tasks import process_study_package


AgentJobStatus = Literal["pending", "processing", "completed", "failed"]


class AgentJobAccepted(BaseModel):
    job_id: str
    status: AgentJobStatus = "pending"
    progress: int = 0


class AgentJobResponse(BaseModel):
    job_id: str
    status: AgentJobStatus
    progress: int = Field(ge=0, le=100)
    result: dict[str, Any] | None = None
    error: str | None = None


def require_agent_key(
    provided_key: Annotated[str | None, Header(alias="X-Agent-API-Key")] = None,
) -> None:
    if settings.api_key and not compare_digest(provided_key or "", settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid agent API key.",
        )


app = FastAPI(title=settings.app_name, version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "cloud-study-agent"}


@app.post(
    "/jobs",
    response_model=AgentJobAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_agent_key)],
)
def create_job(payload: StudyInput) -> AgentJobAccepted:
    try:
        job = process_study_package.delay(payload.model_dump())
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The agent queue is unavailable.",
        ) from exc
    return AgentJobAccepted(job_id=job.id)


@app.get(
    "/jobs/{job_id}",
    response_model=AgentJobResponse,
    dependencies=[Depends(require_agent_key)],
)
def get_job(job_id: str) -> AgentJobResponse:
    job = celery_app.AsyncResult(job_id)
    job_status, progress = _map_celery_state(job.state, job.info)

    if job_status == "completed":
        try:
            result = StudyOutput.model_validate(job.result).to_dict()
        except ValidationError as exc:
            return AgentJobResponse(
                job_id=job_id,
                status="failed",
                progress=100,
                error=f"The agent produced an invalid result: {exc}",
            )
        return AgentJobResponse(job_id=job_id, status=job_status, progress=100, result=result)

    if job_status == "failed":
        return AgentJobResponse(
            job_id=job_id,
            status=job_status,
            progress=100,
            error=_safe_error(job.result),
        )

    return AgentJobResponse(job_id=job_id, status=job_status, progress=progress)


def _map_celery_state(state: str, info: Any) -> tuple[AgentJobStatus, int]:
    if state == states.SUCCESS:
        return "completed", 100
    if state in {states.FAILURE, states.REVOKED}:
        return "failed", 100
    if state == "PROGRESS":
        progress = info.get("progress", 35) if isinstance(info, dict) else 35
        return "processing", max(1, min(int(progress), 99))
    if state in {states.STARTED, states.RECEIVED, states.RETRY}:
        return "processing", 25
    return "pending", 5


def _safe_error(value: Any) -> str:
    message = str(value).strip()
    return message[:500] if message else "The cloud agent job failed."
