from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import httpx
from pydantic import ValidationError

from backend.app.core.config import settings
from worker.app.agents.contracts import StudyInput, StudyOutput


CloudJobStatus = Literal["pending", "processing", "completed", "failed"]


class CloudAgentError(RuntimeError):
    pass


@dataclass(frozen=True)
class CloudAgentJob:
    job_id: str
    status: CloudJobStatus
    progress: int
    result: dict[str, Any] | None = None
    error: str | None = None


class CloudAgentClient:
    def __init__(self, base_url: str, api_key: str, timeout_seconds: float) -> None:
        if not base_url:
            raise CloudAgentError("AGENT_BASE_URL is required when TASK_QUEUE_MODE=cloud.")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def submit(self, study_input: StudyInput) -> str:
        payload = self._request("POST", "/jobs", json=study_input.model_dump())
        job_id = payload.get("job_id")
        if not isinstance(job_id, str) or not job_id:
            raise CloudAgentError("The cloud agent did not return a job ID.")
        return job_id

    def get_job(self, job_id: str) -> CloudAgentJob:
        payload = self._request("GET", f"/jobs/{job_id}")
        job_status = payload.get("status")
        if job_status not in {"pending", "processing", "completed", "failed"}:
            raise CloudAgentError("The cloud agent returned an unknown job status.")

        result = payload.get("result")
        if result is not None:
            try:
                result = StudyOutput.model_validate(result).to_dict()
            except ValidationError as exc:
                raise CloudAgentError("The cloud agent returned an invalid study package.") from exc

        return CloudAgentJob(
            job_id=str(payload.get("job_id") or job_id),
            status=job_status,
            progress=max(0, min(int(payload.get("progress", 0)), 100)),
            result=result,
            error=str(payload["error"]) if payload.get("error") else None,
        )

    def _request(self, method: str, path: str, json: dict | None = None) -> dict[str, Any]:
        headers = {"X-Agent-API-Key": self.api_key} if self.api_key else {}
        try:
            response = httpx.request(
                method,
                f"{self.base_url}{path}",
                headers=headers,
                json=json,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise CloudAgentError(f"Could not communicate with the cloud agent: {exc}") from exc

        if not isinstance(payload, dict):
            raise CloudAgentError("The cloud agent returned an invalid response.")
        return payload


def build_cloud_agent_client() -> CloudAgentClient:
    return CloudAgentClient(
        base_url=settings.agent_base_url,
        api_key=settings.agent_api_key,
        timeout_seconds=settings.agent_http_timeout_seconds,
    )
