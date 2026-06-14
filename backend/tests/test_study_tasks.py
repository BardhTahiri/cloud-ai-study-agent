from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_create_study_task():
    response = client.post(
        "/api/study-tasks",
        json={
            "title": "Cloud Study",
            "prompt": "Focus on important exam topics.",
            "material_text": (
                "Cloud computing provides access to storage, databases, and compute resources. "
                "A cloud AI worker can process academic documents in the background. "
                "The system generates summaries, quizzes, and study plans for students."
            ),
            "source_type": "text",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["result"]["summary"]
    assert payload["result"]["quiz"]
    assert payload["result"]["study_plan"]
