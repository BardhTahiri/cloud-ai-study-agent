import pytest

from worker.app.agents.contracts import StudyPackage
from worker.app.agents.llm_agent import FreeCompatibleStudyAgent, PaidOpenAIStudyAgent
from worker.app.agents.study_agent import StudyInput, detect_agent_tier, generate_study_package


def test_generate_study_package_returns_core_outputs(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "")
    output = generate_study_package(
        StudyInput(
            title="REST APIs",
            prompt="Focus on architecture and HTTP methods",
            material_text=(
                "REST API is an architectural style for web services. "
                "It uses HTTP methods such as GET, POST, PUT, and DELETE. "
                "REST systems are usually stateless and organized around resources. "
                "Students should understand resources, methods, status codes, and request structure."
            ),
        )
    )

    assert output.important_topics
    assert output.summary
    assert output.quiz
    assert output.study_plan
    assert output.generation.tier == "offline"


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("", "offline"),
        ("https://api.openai.com/v1", "paid"),
        ("http://localhost:11434/v1", "free"),
        ("https://openrouter.ai/api/v1", "free"),
    ],
)
def test_agent_tier_is_selected_from_url(url, expected):
    assert detect_agent_tier(url) == expected


def test_free_url_uses_compatible_agent_without_network(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.setenv("FREE_LLM_MODEL", "test-free-model")

    package = StudyPackage(
        title="Cloud Agents",
        important_topics=["Queues"],
        summary=["Queues move long-running work outside the API request."],
        quiz=[
            {
                "question": "What moves work outside the API request?",
                "answer": "A task queue",
                "topic": "Queues",
                "options": ["A task queue", "A stylesheet", "A browser cookie"],
                "correct_option": "A task queue",
            }
        ],
        study_plan=[{"day": 1, "focus": "Queues", "tasks": ["Review queue behavior."]}],
    )
    monkeypatch.setattr(FreeCompatibleStudyAgent, "generate", lambda self, study_input: package)

    output = generate_study_package(
        StudyInput(
            title="Cloud Agents",
            prompt="Focus on queues.",
            material_text=(
                "A task queue moves long-running work outside the API request. "
                "Workers process jobs and save their results for the user."
            ),
        )
    )

    assert output.generation.tier == "free"
    assert output.generation.model == "test-free-model"


def test_openai_url_uses_paid_agent_without_network(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("PAID_LLM_MODEL", "test-paid-model")

    package = StudyPackage(
        title="Paid Agent",
        important_topics=["Structured Output"],
        summary=["The paid agent returns a validated study package."],
        quiz=[
            {
                "question": "What does the paid agent return?",
                "answer": "A validated study package",
                "topic": "Structured Output",
                "options": ["A validated study package", "An image", "A database password"],
                "correct_option": "A validated study package",
            }
        ],
        study_plan=[{"day": 1, "focus": "Structured Output", "tasks": ["Review the package."]}],
    )
    monkeypatch.setattr(PaidOpenAIStudyAgent, "generate", lambda self, study_input: package)

    output = generate_study_package(
        StudyInput(
            title="Paid Agent",
            prompt="Focus on structured output.",
            material_text=(
                "A paid model can produce a validated structured study package. "
                "The worker stores that package after background processing."
            ),
        )
    )

    assert output.generation.tier == "paid"
    assert output.generation.provider == "openai"
    assert output.generation.model == "test-paid-model"
