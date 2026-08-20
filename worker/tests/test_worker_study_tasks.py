import pytest

from worker.app.agents.study_agent import StudyAgentUnavailableError
from worker.app.jobs import study_tasks


STUDY_INPUT = {
    "title": "Durable retries",
    "prompt": "Focus on background processing.",
    "material_text": (
        "A cloud worker can retry temporary provider failures while the student's computer is off. "
        "The completed result remains available for the local backend to collect later."
    ),
}


def test_provider_unavailability_reschedules_the_cloud_job(monkeypatch):
    captured_retry = {}

    class RetryRequested(Exception):
        pass

    def request_retry(**kwargs):
        captured_retry.update(kwargs)
        return RetryRequested()

    monkeypatch.setattr(study_tasks.settings, "provider_retry_delay_seconds", 300)
    monkeypatch.setattr(study_tasks.settings, "provider_max_retries", 288)
    monkeypatch.setattr(
        study_tasks.process_study_package,
        "update_state",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(study_tasks.process_study_package, "retry", request_retry)

    def unavailable(study_input):
        raise StudyAgentUnavailableError("Codex is temporarily unavailable")

    monkeypatch.setattr(study_tasks, "generate_study_package", unavailable)

    with pytest.raises(RetryRequested):
        study_tasks.process_study_package.run(STUDY_INPUT)

    assert isinstance(captured_retry["exc"], StudyAgentUnavailableError)
    assert captured_retry["countdown"] == 300
    assert captured_retry["max_retries"] == 288
