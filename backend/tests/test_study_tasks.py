from backend.app.main import app
from backend.app.schemas.study import StudyTaskCreate
from backend.app.services.file_service import clean_extracted_text
from fastapi.testclient import TestClient


def test_create_study_task():
    with TestClient(app) as client:
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

        assert response.status_code == 202
        created = response.json()
        assert created["status"] == "pending"

        task_response = client.get(f"/api/study-tasks/{created['id']}")
        assert task_response.status_code == 200
        payload = task_response.json()
        assert payload["status"] == "completed"
        assert payload["result"]["summary"]
        assert payload["result"]["quiz"]
        assert len(payload["result"]["quiz"][0]["options"]) == 4
        assert payload["result"]["quiz"][0]["correct_option"] in payload["result"]["quiz"][0]["options"]
        assert payload["result"]["study_plan"]


def test_delete_study_task():
    with TestClient(app) as client:
        response = client.post(
            "/api/study-tasks",
            json={
                "title": "Delete Me",
                "prompt": "Create a short quiz.",
                "material_text": (
                    "Students use summaries and quizzes to study more effectively. "
                    "The AI study agent creates a study plan from academic material. "
                    "Deleting old tasks keeps the recent task list clean."
                ),
                "source_type": "text",
            },
        )

        assert response.status_code == 202
        task_id = response.json()["id"]

        delete_response = client.delete(f"/api/study-tasks/{task_id}")
        assert delete_response.status_code == 204

        missing_response = client.get(f"/api/study-tasks/{task_id}")
        assert missing_response.status_code == 404


def test_clean_extracted_text_removes_invalid_unicode_for_uploads():
    raw_text = (
        "Artificial Intelligence Report 2026 \udcff "
        "This material explains machine learning, neural networks, cloud agents, "
        "study plans, quizzes, summaries, and important academic topics."
    )

    cleaned_text = clean_extracted_text(raw_text)

    payload = StudyTaskCreate(
        title="AI Report",
        prompt="Build a study plan.",
        material_text=cleaned_text,
        source_type="pdf",
    )

    assert "\udcff" not in payload.material_text
    assert "Artificial Intelligence" in payload.material_text
