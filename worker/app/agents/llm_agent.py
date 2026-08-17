from __future__ import annotations

import json
from dataclasses import dataclass

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
Follow the student's focus request when it is relevant. Do not include facts unsupported by the material."""


@dataclass(frozen=True)
class LlmAgentConfig:
    base_url: str
    model: str
    api_key: str
    timeout_seconds: float
    max_input_chars: int


class PaidOpenAIStudyAgent:
    tier = "paid"
    provider = "openai"

    def __init__(self, config: LlmAgentConfig):
        if not config.api_key:
            raise ValueError("OPENAI_API_KEY is required for the paid OpenAI agent.")
        self.config = config
        self.model = config.model
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout_seconds,
        )

    def generate(self, study_input: StudyInput) -> StudyPackage:
        response = self.client.responses.parse(
            model=self.model,
            input=_messages(study_input, self.config.max_input_chars),
            text_format=StudyPackage,
        )
        if response.output_parsed is None:
            raise ValueError("The paid model did not return a study package.")
        return response.output_parsed


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
            response_format={"type": "json_object"},
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
