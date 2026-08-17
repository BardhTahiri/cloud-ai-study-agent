from types import SimpleNamespace

from celery import states
from fastapi.testclient import TestClient

from worker.app import api as agent_api


STUDY_INPUT = {
    "title": "Cloud queues",
    "prompt": "Focus on background processing.",
    "material_text": (
        "A cloud queue lets an API submit work without performing generation in the request. "
        "A worker receives the queued material and generates a structured study package."
    ),
}

STUDY_OUTPUT = {
    "title": "Cloud queues",
    "important_topics": ["Queues"],
    "summary": ["Queues connect the agent API to a background worker."],
    "quiz": [
        {
            "question": "What connects the API and worker?",
            "answer": "A queue",
            "topic": "Queues",
            "options": ["A queue", "A stylesheet", "A browser cookie"],
            "correct_option": "A queue",
        }
    ],
    "study_plan": [{"day": 1, "focus": "Queues", "tasks": ["Review queue behavior."]}],
    "generation": {
        "tier": "offline",
        "provider": "deterministic",
        "model": "local-rules",
        "fallback_reason": None,
    },
}


def test_agent_api_requires_configured_key(monkeypatch):
    monkeypatch.setattr(agent_api.settings, "api_key", "test-secret")

    with TestClient(agent_api.app) as client:
        response = client.post("/jobs", json=STUDY_INPUT)

    assert response.status_code == 401


def test_agent_api_submits_job_and_returns_result(monkeypatch):
    monkeypatch.setattr(agent_api.settings, "api_key", "test-secret")
    monkeypatch.setattr(
        agent_api.process_study_package,
        "delay",
        lambda payload: SimpleNamespace(id="cloud-job-1"),
    )

    with TestClient(agent_api.app) as client:
        accepted = client.post(
            "/jobs",
            json=STUDY_INPUT,
            headers={"X-Agent-API-Key": "test-secret"},
        )

        assert accepted.status_code == 202
        assert accepted.json() == {"job_id": "cloud-job-1", "status": "pending", "progress": 0}

        fake_result = SimpleNamespace(state=states.SUCCESS, info=STUDY_OUTPUT, result=STUDY_OUTPUT)
        monkeypatch.setattr(agent_api.celery_app, "AsyncResult", lambda job_id: fake_result)
        completed = client.get(
            "/jobs/cloud-job-1",
            headers={"X-Agent-API-Key": "test-secret"},
        )

    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    assert completed.json()["result"] == STUDY_OUTPUT
