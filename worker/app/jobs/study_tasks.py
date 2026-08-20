from worker.app.agents.contracts import StudyInput
from worker.app.agents.study_agent import StudyAgentUnavailableError, generate_study_package
from worker.app.celery_app import celery_app
from worker.app.config import settings


@celery_app.task(
    bind=True,
    name="study_agent.generate",
)
def process_study_package(self, payload: dict) -> dict:
    study_input = StudyInput.model_validate(payload)
    self.update_state(state="PROGRESS", meta={"progress": 35})
    try:
        result = generate_study_package(study_input)
    except StudyAgentUnavailableError as exc:
        raise self.retry(
            exc=exc,
            countdown=settings.provider_retry_delay_seconds,
            max_retries=settings.provider_max_retries,
        ) from exc
    return result.to_dict()
