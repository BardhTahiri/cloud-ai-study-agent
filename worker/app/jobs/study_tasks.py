from worker.app.agents.contracts import StudyInput
from worker.app.agents.study_agent import generate_study_package
from worker.app.celery_app import celery_app


@celery_app.task(
    bind=True,
    name="study_agent.generate",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 2},
)
def process_study_package(self, payload: dict) -> dict:
    study_input = StudyInput.model_validate(payload)
    self.update_state(state="PROGRESS", meta={"progress": 35})
    result = generate_study_package(study_input)
    return result.to_dict()
