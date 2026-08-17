from __future__ import annotations

import logging

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.models import StudyTaskRecord
from backend.app.models.entities import TaskStatus, utc_now
from backend.app.services import study_service
from backend.app.services.cloud_agent_client import build_cloud_agent_client
from worker.app.agents.contracts import StudyInput


logger = logging.getLogger(__name__)


def dispatch_study_task(task: StudyTaskRecord, background_tasks: BackgroundTasks, db: Session) -> None:
    if settings.task_queue_mode == "local":
        background_tasks.add_task(study_service.run_study_task, task.id)
        return

    if settings.task_queue_mode != "cloud":
        raise RuntimeError("TASK_QUEUE_MODE must be either 'local' or 'cloud'.")

    try:
        job_id = build_cloud_agent_client().submit(
            StudyInput(title=task.title, prompt=task.prompt, material_text=task.material_text)
        )
        task.agent_job_id = job_id
        task.status = TaskStatus.pending.value
        task.progress = 5
        task.updated_at = utc_now()
        db.commit()
        db.refresh(task)
    except Exception as exc:
        logger.exception("Could not submit study task %s to the cloud agent.", task.id)
        if settings.task_queue_fallback_local:
            background_tasks.add_task(study_service.run_study_task, task.id)
            return

        study_service.mark_dispatch_failed(task.id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The cloud agent is unavailable. Please try again.",
        ) from exc
