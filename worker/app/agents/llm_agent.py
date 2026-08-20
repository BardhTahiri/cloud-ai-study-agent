from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from openai import OpenAI

from worker.app.agents.contracts import StudyInput, StudyPackage
from worker.app.processors.text_processor import extract_topics, normalize_text, select_key_sentences


SYSTEM_PROMPT = """You are a study-package agent. Use only the supplied academic material as the source of truth.
Create an exam-focused package with:
- 5 to 10 important topics
- 3 to 8 concise summary points
- 4 to 8 multiple-choice quiz questions, each with 3 or 4 plausible options
- the correct option copied exactly into both answer and correct_option
- a practical study plan of 3 to 7 days
Follow the student's focus request when it is relevant. Do not include facts unsupported by the material.
Return only one valid JSON object with these keys: title, important_topics, summary, quiz, and study_plan.
Do not wrap the JSON in a Markdown code fence or include commentary outside the JSON object."""


@dataclass(frozen=True)
class LlmAgentConfig:
    base_url: str
    model: str
    api_key: str
    timeout_seconds: float
    max_input_chars: int
    max_output_tokens: int | None = None


@dataclass(frozen=True)
class CodexAgentConfig:
    model: str
    codex_bin: str
    codex_home: str
    timeout_seconds: float
    max_input_chars: int


class CodexSubscriptionStudyAgent:
    tier = "codex"
    provider = "chatgpt-codex"

    def __init__(self, config: CodexAgentConfig):
        self.config = config
        self.model = config.model

    def generate(self, study_input: StudyInput) -> StudyPackage:
        material = _prepare_material(
            study_input.material_text,
            study_input.prompt,
            self.config.max_input_chars,
        )
        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"Package title: {study_input.title}\n"
            f"Student focus: {study_input.prompt or 'Identify the most important exam material.'}\n\n"
            "The academic material is supplied through standard input. Analyze only that material "
            "and return the schema-constrained study package. Do not inspect files or run tools."
        )

        schema_path = Path(__file__).with_name("study_package.schema.json").resolve()
        command = [
            self.config.codex_bin,
            "exec",
            "--ephemeral",
            "--sandbox",
            "read-only",
            "--skip-git-repo-check",
            "--ignore-user-config",
            "--ignore-rules",
            "--model",
            self.model,
            "--output-schema",
            str(schema_path),
            prompt,
        ]
        try:
            completed = subprocess.run(
                command,
                input=f"Academic material:\n{material}",
                text=True,
                capture_output=True,
                check=False,
                cwd=os.getenv("CODEX_WORK_DIR") or tempfile.gettempdir(),
                env=_codex_environment(self.config.codex_home),
                timeout=self.config.timeout_seconds,
                encoding="utf-8",
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                f"Codex CLI was not found at {self.config.codex_bin!r}."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"Codex did not finish within {self.config.timeout_seconds:g} seconds."
            ) from exc

        if completed.returncode != 0:
            details = _command_error(completed.stderr)
            raise RuntimeError(f"Codex generation failed: {details}")
        if not completed.stdout.strip():
            raise ValueError("Codex completed without returning a study package.")
        return StudyPackage.model_validate_json(_strip_code_fence(completed.stdout))


class FreeCompatibleStudyAgent:
    tier = "free"
    provider = "openai-compatible"

    def __init__(self, config: LlmAgentConfig):
        self.config = config
        self.model = config.model
        self.client = OpenAI(
            api_key=config.api_key or "local-model",
            base_url=config.base_url,
            timeout=config.timeout_seconds,
        )

    def generate(self, study_input: StudyInput) -> StudyPackage:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=_messages(study_input, self.config.max_input_chars),
            response_format=_compatible_response_format(self.config.base_url),
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("The free model did not return a study package.")
        return StudyPackage.model_validate(json.loads(_strip_code_fence(content)))


def _messages(study_input: StudyInput, max_input_chars: int) -> list[dict[str, str]]:
    material = _prepare_material(study_input.material_text, study_input.prompt, max_input_chars)
    user_prompt = (
        f"Package title: {study_input.title}\n"
        f"Student focus: {study_input.prompt or 'Identify the most important exam material.'}\n\n"
        f"Academic material:\n{material}"
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def _prepare_material(material_text: str, prompt: str, max_input_chars: int) -> str:
    material = normalize_text(material_text)
    if len(material) <= max_input_chars:
        return material

    topics = extract_topics(f"{prompt} {material}", limit=20)
    sentences = select_key_sentences(material, topics, prompt, limit=160)
    reduced = " ".join(sentences)
    return reduced[:max_input_chars]


def _strip_code_fence(content: str) -> str:
    stripped = content.strip()
    if not stripped.startswith("```"):
        return stripped

    first_newline = stripped.find("\n")
    if first_newline == -1:
        return stripped
    stripped = stripped[first_newline + 1 :]
    if stripped.endswith("```"):
        stripped = stripped[:-3]
    return stripped.strip()


def _codex_environment(codex_home: str) -> dict[str, str]:
    allowed_names = {
        "CODEX_CA_CERTIFICATE",
        "COMSPEC",
        "HOME",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "LANG",
        "LC_ALL",
        "NO_PROXY",
        "PATH",
        "PATHEXT",
        "SSL_CERT_DIR",
        "SSL_CERT_FILE",
        "SYSTEMROOT",
        "TEMP",
        "TERM",
        "TMP",
        "TMPDIR",
        "USER",
    }
    environment = {
        name: value
        for name, value in os.environ.items()
        if name.upper() in allowed_names
    }
    environment.setdefault("PATH", os.defpath)
    environment["CODEX_HOME"] = codex_home
    return environment


def _command_error(stderr: str) -> str:
    details = stderr.strip()
    if not details:
        return "the Codex process exited without an error message"
    return details[-1000:]


def _compatible_response_format(base_url: str) -> dict[str, Any]:
    if urlparse(base_url).hostname == "api.groq.com":
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "study_package",
                "strict": True,
                "schema": _strict_study_package_schema(),
            },
        }
    return {"type": "json_object"}


def _strict_study_package_schema() -> dict[str, Any]:
    schema = StudyPackage.model_json_schema()
    _forbid_extra_object_properties(schema)
    return schema


def _forbid_extra_object_properties(value: Any) -> None:
    if isinstance(value, dict):
        if value.get("type") == "object":
            value["additionalProperties"] = False
        for child in value.values():
            _forbid_extra_object_properties(child)
    elif isinstance(value, list):
        for child in value:
            _forbid_extra_object_properties(child)
