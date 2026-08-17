from celery import Celery

from worker.app.config import settings


celery_app = Celery(
    "cloud_ai_study_agent",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["worker.app.jobs.study_tasks"],
)
celery_app.conf.update(
    broker_connection_retry_on_startup=True,
    task_acks_late=True,
    task_ignore_result=False,
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_accept_content=["json"],
    result_expires=settings.result_expires_seconds,
    timezone="UTC",
)
