import os

os.environ["DATABASE_URL"] = "sqlite:///./storage/test_cloud_ai_study_agent.db"
os.environ["TASK_QUEUE_MODE"] = "local"
os.environ["LLM_BASE_URL"] = ""

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.db.session import SessionLocal
from backend.app.schemas.study import StudyTaskCreate
from backend.app.services import study_service, task_dispatcher
from backend.app.services.cloud_agent_client import CloudAgentJob
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
        assert payload["result"]["generation"]["tier"] == "offline"


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


def test_cloud_mode_submits_material_and_saves_remote_result(monkeypatch):
    submitted_inputs = []
    generated_result = {
        "title": "Cloud Worker",
        "important_topics": ["Remote jobs"],
        "summary": ["The local backend delegates generation to a cloud worker."],
        "quiz": [
            {
                "question": "Where does generation run?",
                "answer": "In the cloud worker",
                "topic": "Remote jobs",
                "options": ["In the cloud worker", "In CSS", "In the browser cookie"],
                "correct_option": "In the cloud worker",
            }
        ],
        "study_plan": [{"day": 1, "focus": "Remote jobs", "tasks": ["Review the job flow."]}],
        "generation": {
            "tier": "offline",
            "provider": "deterministic",
            "model": "local-rules",
            "fallback_reason": None,
        },
    }

    class FakeCloudAgentClient:
        def submit(self, study_input):
            submitted_inputs.append(study_input)
            return "agent-job-123"

        def get_job(self, job_id):
            assert job_id == "agent-job-123"
            return CloudAgentJob(
                job_id=job_id,
                status="completed",
                progress=100,
                result=generated_result,
            )

    fake_client = FakeCloudAgentClient()
    monkeypatch.setattr(settings, "task_queue_mode", "cloud")
    monkeypatch.setattr(settings, "task_queue_fallback_local", False)
    monkeypatch.setattr(task_dispatcher, "build_cloud_agent_client", lambda: fake_client)
    monkeypatch.setattr(study_service, "build_cloud_agent_client", lambda: fake_client)

    with TestClient(app) as client:
        response = client.post(
            "/api/study-tasks",
            json={
                "title": "Cloud Worker",
                "prompt": "Focus on remote execution.",
                "material_text": (
                    "The local application sends study material to a cloud agent API. "
                    "A background worker generates the package and returns it later."
                ),
                "source_type": "text",
            },
        )

        assert response.status_code == 202
        created = response.json()
        assert created["status"] == "pending"
        assert created["progress"] == 5
        assert submitted_inputs[0].title == "Cloud Worker"
        assert "cloud agent API" in submitted_inputs[0].material_text

        task_response = client.get(f"/api/study-tasks/{created['id']}")
        assert task_response.status_code == 200
        completed = task_response.json()
        assert completed["status"] == "completed"
        assert completed["result"] == generated_result


def test_cloud_mode_recovers_pending_task_without_job_id(monkeypatch):
    submitted_ids = []
    generated_result = {
        "title": "Recovered Cloud Task",
        "important_topics": ["Recovery"],
        "summary": ["Pending tasks without a cloud job ID are submitted again."],
        "quiz": [
            {
                "question": "What happens to an orphaned pending task?",
                "answer": "It is submitted again",
                "topic": "Recovery",
                "options": ["It is submitted again", "It polls forever", "It is hidden"],
                "correct_option": "It is submitted again",
            }
        ],
        "study_plan": [{"day": 1, "focus": "Recovery", "tasks": ["Review recovery behavior."]}],
        "generation": {
            "tier": "free",
            "provider": "openai-compatible",
            "model": "test-free-model",
            "fallback_reason": None,
        },
    }

    class FakeCloudAgentClient:
        def submit(self, study_input):
            submitted_ids.append(study_input.title)
            return "recovered-job-123"

        def get_job(self, job_id):
            assert job_id == "recovered-job-123"
            return CloudAgentJob(
                job_id=job_id,
                status="completed",
                progress=100,
                result=generated_result,
            )

    fake_client = FakeCloudAgentClient()
    monkeypatch.setattr(settings, "task_queue_mode", "cloud")
    monkeypatch.setattr(study_service, "build_cloud_agent_client", lambda: fake_client)

    with SessionLocal() as db:
        task = study_service.create_study_task(
            db,
            StudyTaskCreate(
                title="Recovered Cloud Task",
                prompt="Focus on recovery.",
                material_text=(
                    "A task can remain pending if a process stops before its cloud job ID is stored. "
                    "The backend should recover that task instead of polling it forever."
                ),
                source_type="text",
            ),
        )
        task_id = task.id

    with TestClient(app) as client:
        response = client.get(f"/api/study-tasks/{task_id}")

    assert response.status_code == 200
    recovered = response.json()
    assert recovered["status"] == "completed"
    assert recovered["progress"] == 100
    assert recovered["result"] == generated_result
    assert submitted_ids == ["Recovered Cloud Task"]
