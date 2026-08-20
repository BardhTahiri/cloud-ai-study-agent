from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class StudyInput(BaseModel):
    title: str
    prompt: str
    material_text: str


class QuizQuestion(BaseModel):
    question: str
    answer: str
    topic: str
    options: list[str] = Field(min_length=3, max_length=4)
    correct_option: str

    @model_validator(mode="after")
    def correct_option_must_be_available(self) -> "QuizQuestion":
        if self.correct_option not in self.options:
            raise ValueError("correct_option must be one of the quiz options")
        if self.answer != self.correct_option:
            raise ValueError("answer and correct_option must match")
        if len(set(self.options)) != len(self.options):
            raise ValueError("quiz options must be unique")
        return self


class StudyPlanDay(BaseModel):
    day: int
    focus: str
    tasks: list[str]


class StudyPackage(BaseModel):
    title: str
    important_topics: list[str] = Field(min_length=1, max_length=10)
    summary: list[str] = Field(min_length=1, max_length=8)
    quiz: list[QuizQuestion] = Field(min_length=1, max_length=8)
    study_plan: list[StudyPlanDay] = Field(min_length=1, max_length=7)


class GenerationMetadata(BaseModel):
    tier: Literal["offline", "free", "codex"]
    provider: str
    model: str
    fallback_reason: str | None = None


class StudyOutput(StudyPackage):
    generation: GenerationMetadata

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()
