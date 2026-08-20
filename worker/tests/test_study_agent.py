import json
import subprocess
from pathlib import Path

import pytest

from worker.app.agents.contracts import StudyPackage
from worker.app.agents.llm_agent import (
    SYSTEM_PROMPT,
    CodexAgentConfig,
    CodexSubscriptionStudyAgent,
    FreeCompatibleStudyAgent,
    _compatible_response_format,
)
from worker.app.agents.study_agent import (
    AgentSettings,
    StudyInput,
    _build_llm_agent,
    detect_agent_tier,
    generate_study_package,
)


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
        ("codex://subscription", "codex"),
        ("http://localhost:11434/v1", "free"),
        ("https://openrouter.ai/api/v1", "free"),
    ],
)
def test_agent_tier_is_selected_from_url(url, expected):
    assert detect_agent_tier(url) == expected


def test_openai_api_url_is_rejected_after_paid_provider_removal():
    with pytest.raises(ValueError, match="paid OpenAI API provider was removed"):
        detect_agent_tier("https://api.openai.com/v1")


def test_system_prompt_explicitly_requests_json():
    assert "json" in SYSTEM_PROMPT.lower()


def test_groq_uses_strict_json_schema():
    response_format = _compatible_response_format("https://api.groq.com/openai/v1")
    schema = response_format["json_schema"]["schema"]

    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True
    assert schema["additionalProperties"] is False
    assert all(definition["additionalProperties"] is False for definition in schema["$defs"].values())


def test_other_compatible_providers_use_json_object_mode():
    assert _compatible_response_format("http://localhost:11434/v1") == {"type": "json_object"}


def test_free_agent_caps_material_but_codex_keeps_configured_limit():
    settings = AgentSettings(
        base_url="https://api.groq.com/openai/v1",
        free_model="free-model",
        codex_model="gpt-5.6-sol",
        free_api_key="free-key",
        codex_bin="codex",
        codex_home="/codex-auth",
        timeout_seconds=120,
        codex_timeout_seconds=300,
        max_input_chars=100000,
        free_max_input_chars=12000,
        fallback_to_offline=True,
    )

    free_agent = _build_llm_agent(settings, "free")
    codex_agent = _build_llm_agent(settings, "codex")

    assert free_agent.config.max_input_chars == 12000
    assert codex_agent.config.max_input_chars == 100000
    assert codex_agent.config.timeout_seconds == 300
    assert codex_agent.config.codex_home == "/codex-auth"


def test_codex_agent_uses_subscription_auth_and_strict_read_only_output(monkeypatch):
    package = StudyPackage(
        title="Codex Study Package",
        important_topics=["Structured output"],
        summary=["Codex validates the generated package against a JSON schema."],
        quiz=[
            {
                "question": "What validates the package?",
                "answer": "A Pydantic schema",
                "topic": "Structured output",
                "options": ["A Pydantic schema", "A CSS rule", "A database index"],
                "correct_option": "A Pydantic schema",
            }
        ],
        study_plan=[{"day": 1, "focus": "Structured output", "tasks": ["Review the schema."]}],
    )
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured.update(kwargs)
        schema_path = Path(command[command.index("--output-schema") + 1])
        captured["schema"] = json.loads(schema_path.read_text(encoding="utf-8"))
        return subprocess.CompletedProcess(command, 0, package.model_dump_json(), "")

    monkeypatch.setattr("worker.app.agents.llm_agent.subprocess.run", fake_run)
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-be-forwarded")
    monkeypatch.setenv("CODEX_API_KEY", "must-not-be-forwarded")
    monkeypatch.setenv("LLM_API_KEY", "must-not-be-forwarded")
    monkeypatch.setenv("REDIS_URL", "must-not-be-forwarded")

    agent = CodexSubscriptionStudyAgent(
        config=CodexAgentConfig(
            model="gpt-5.6-sol",
            codex_bin="codex",
            codex_home="/codex-auth",
            timeout_seconds=300,
            max_input_chars=100000,
        )
    )

    output = agent.generate(
        StudyInput(
            title="Codex Study Package",
            prompt="Focus on structured output.",
            material_text="Structured outputs validate model responses against a supplied schema.",
        )
    )

    assert output == package
    assert captured["command"][:2] == ["codex", "exec"]
    assert "--ephemeral" in captured["command"]
    assert captured["command"][captured["command"].index("--sandbox") + 1] == "read-only"
    assert captured["command"][captured["command"].index("--model") + 1] == "gpt-5.6-sol"
    assert "Structured outputs validate" in captured["input"]
    assert captured["env"]["CODEX_HOME"] == "/codex-auth"
    assert "OPENAI_API_KEY" not in captured["env"]
    assert "CODEX_API_KEY" not in captured["env"]
    assert "LLM_API_KEY" not in captured["env"]
    assert "REDIS_URL" not in captured["env"]
    assert captured["schema"]["additionalProperties"] is False


def test_codex_schema_asset_matches_the_pydantic_contract():
    schema_path = Path("worker/app/agents/study_package.schema.json")
    assert json.loads(schema_path.read_text(encoding="utf-8")) == _compatible_response_format(
        "https://api.groq.com/openai/v1"
    )["json_schema"]["schema"]


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


def test_codex_url_uses_subscription_agent_without_network(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "codex://subscription")
    monkeypatch.setenv("CODEX_MODEL", "test-codex-model")

    package = StudyPackage(
        title="Codex Agent",
        important_topics=["Structured Output"],
        summary=["The Codex agent returns a validated study package."],
        quiz=[
            {
                "question": "What does the Codex agent return?",
                "answer": "A validated study package",
                "topic": "Structured Output",
                "options": ["A validated study package", "An image", "A database password"],
                "correct_option": "A validated study package",
            }
        ],
        study_plan=[{"day": 1, "focus": "Structured Output", "tasks": ["Review the package."]}],
    )
    monkeypatch.setattr(CodexSubscriptionStudyAgent, "generate", lambda self, study_input: package)

    output = generate_study_package(
        StudyInput(
            title="Codex Agent",
            prompt="Focus on structured output.",
            material_text=(
                "Codex can produce a validated structured study package. "
                "The worker stores that package after background processing."
            ),
        )
    )

    assert output.generation.tier == "codex"
    assert output.generation.provider == "chatgpt-codex"
    assert output.generation.model == "test-codex-model"
