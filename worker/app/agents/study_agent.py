from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from urllib.parse import urlparse

from worker.app.agents.contracts import GenerationMetadata, StudyInput, StudyOutput, StudyPackage
from worker.app.agents.deterministic_agent import generate_deterministic_package
from worker.app.agents.llm_agent import (
    CodexAgentConfig,
    CodexSubscriptionStudyAgent,
    FreeCompatibleStudyAgent,
    LlmAgentConfig,
)


logger = logging.getLogger(__name__)
CODEX_SUBSCRIPTION_URL = "codex://subscription"


@dataclass(frozen=True)
class AgentSettings:
    base_url: str
    free_model: str
    codex_model: str
    free_api_key: str
    codex_bin: str
    codex_home: str
    timeout_seconds: float
    codex_timeout_seconds: float
    max_input_chars: int
    free_max_input_chars: int
    fallback_to_offline: bool

    @classmethod
    def from_env(cls) -> "AgentSettings":
        return cls(
            base_url=os.getenv("LLM_BASE_URL", "").strip().rstrip("/"),
            free_model=os.getenv("FREE_LLM_MODEL", "qwen3:8b"),
            codex_model=os.getenv("CODEX_MODEL", "gpt-5.6-sol"),
            free_api_key=os.getenv("LLM_API_KEY", ""),
            codex_bin=os.getenv("CODEX_BIN", "codex"),
            codex_home=os.getenv("CODEX_HOME", "~/.codex"),
            timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "120")),
            codex_timeout_seconds=float(os.getenv("CODEX_TIMEOUT_SECONDS", "300")),
            max_input_chars=int(os.getenv("LLM_MAX_INPUT_CHARS", "100000")),
            free_max_input_chars=int(os.getenv("FREE_LLM_MAX_INPUT_CHARS", "12000")),
            fallback_to_offline=_env_bool("LLM_FALLBACK_TO_OFFLINE", default=True),
        )


def generate_study_package(study_input: StudyInput) -> StudyOutput:
    settings = AgentSettings.from_env()
    tier = detect_agent_tier(settings.base_url)

    if tier == "offline":
        package = generate_deterministic_package(study_input)
        return _with_metadata(package, "offline", "deterministic", "local-rules")

    try:
        agent = _build_llm_agent(settings, tier)
        package = agent.generate(study_input)
        return _with_metadata(package, agent.tier, agent.provider, agent.model)
    except Exception as exc:
        if not settings.fallback_to_offline:
            raise RuntimeError(f"{tier.capitalize()} study agent failed: {exc}") from exc

        logger.exception("Configured %s study agent failed; using the offline generator.", tier)
        package = generate_deterministic_package(study_input)
        reason = f"{exc.__class__.__name__}: {str(exc)[:300]}"
        return _with_metadata(package, "offline", "deterministic", "local-rules", reason)


def detect_agent_tier(base_url: str) -> str:
    if not base_url:
        return "offline"
    if base_url.lower() == CODEX_SUBSCRIPTION_URL:
        return "codex"

    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(
            f"LLM_BASE_URL must be {CODEX_SUBSCRIPTION_URL!r} or an absolute http/https URL."
        )
    if parsed.hostname.lower() == "api.openai.com":
        raise ValueError(
            f"The paid OpenAI API provider was removed. Use {CODEX_SUBSCRIPTION_URL!r} "
            "for ChatGPT subscription access."
        )
    return "free"


def _build_llm_agent(settings: AgentSettings, tier: str):
    if tier == "codex":
        config = CodexAgentConfig(
            model=settings.codex_model,
            codex_bin=settings.codex_bin,
            codex_home=os.path.expanduser(settings.codex_home),
            timeout_seconds=settings.codex_timeout_seconds,
            max_input_chars=settings.max_input_chars,
        )
        return CodexSubscriptionStudyAgent(config)

    config = LlmAgentConfig(
        base_url=settings.base_url,
        model=settings.free_model,
        api_key=settings.free_api_key,
        timeout_seconds=settings.timeout_seconds,
        max_input_chars=min(settings.max_input_chars, settings.free_max_input_chars),
    )
    return FreeCompatibleStudyAgent(config)


def _with_metadata(
    package: StudyPackage,
    tier: str,
    provider: str,
    model: str,
    fallback_reason: str | None = None,
) -> StudyOutput:
    return StudyOutput(
        **package.model_dump(),
        generation=GenerationMetadata(
            tier=tier,
            provider=provider,
            model=model,
            fallback_reason=fallback_reason,
        ),
    )


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}
