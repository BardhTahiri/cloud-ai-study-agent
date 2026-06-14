from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any

from worker.app.processors.text_processor import extract_topics, normalize_text, select_key_sentences


@dataclass
class StudyInput:
    title: str
    prompt: str
    material_text: str


@dataclass
class QuizQuestion:
    question: str
    answer: str
    topic: str

    def to_dict(self) -> dict[str, str]:
        return {
            "question": self.question,
            "answer": self.answer,
            "topic": self.topic,
        }


@dataclass
class StudyPlanDay:
    day: int
    focus: str
    tasks: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "day": self.day,
            "focus": self.focus,
            "tasks": self.tasks,
        }


@dataclass
class StudyOutput:
    title: str
    important_topics: list[str]
    summary: list[str]
    quiz: list[QuizQuestion]
    study_plan: list[StudyPlanDay]

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "important_topics": self.important_topics,
            "summary": self.summary,
            "quiz": [question.to_dict() for question in self.quiz],
            "study_plan": [day.to_dict() for day in self.study_plan],
        }


def generate_study_package(study_input: StudyInput) -> StudyOutput:
    material = normalize_text(study_input.material_text)
    if len(material) < 30:
        raise ValueError("Material is too short to generate a study package.")

    topics = extract_topics(f"{study_input.prompt} {material}", limit=8)
    summary = select_key_sentences(material, topics, study_input.prompt, limit=5)
    quiz = _generate_quiz(topics, summary)
    study_plan = _generate_study_plan(topics, summary)

    return StudyOutput(
        title=study_input.title,
        important_topics=topics,
        summary=summary,
        quiz=quiz,
        study_plan=study_plan,
    )


def _generate_quiz(topics: list[str], summary: list[str]) -> list[QuizQuestion]:
    questions: list[QuizQuestion] = []
    fallback_answer = summary[0] if summary else "Review the uploaded material and explain the topic in your own words."

    for index, topic in enumerate(topics[:6], start=1):
        answer = _find_sentence_for_topic(topic, summary) or fallback_answer
        questions.append(
            QuizQuestion(
                question=f"{index}. Explain why '{topic}' is important in this material.",
                answer=answer,
                topic=topic,
            )
        )

    if not questions:
        questions.append(
            QuizQuestion(
                question="1. What is the main idea of this material?",
                answer=fallback_answer,
                topic="Main Idea",
            )
        )

    return questions


def _generate_study_plan(topics: list[str], summary: list[str]) -> list[StudyPlanDay]:
    if not topics:
        topics = ["Main Idea", "Key Concepts", "Review"]

    day_count = min(max(ceil(len(topics) / 2), 3), 5)
    chunk_size = ceil(len(topics) / day_count)
    days: list[StudyPlanDay] = []

    for day in range(day_count):
        day_topics = topics[day * chunk_size : (day + 1) * chunk_size] or topics[-1:]
        focus = ", ".join(day_topics)
        days.append(
            StudyPlanDay(
                day=day + 1,
                focus=focus,
                tasks=[
                    f"Read the section related to {focus}.",
                    "Write a short explanation using your own words.",
                    "Answer the generated quiz questions for this focus area.",
                    _review_task(day, summary),
                ],
            )
        )

    return days


def _find_sentence_for_topic(topic: str, sentences: list[str]) -> str | None:
    topic_lower = topic.lower()
    for sentence in sentences:
        if topic_lower in sentence.lower():
            return sentence
    return None


def _review_task(day_index: int, summary: list[str]) -> str:
    if not summary:
        return "Create one example that connects the topic to a real academic problem."

    sentence = summary[min(day_index, len(summary) - 1)]
    return f"Review this key point: {sentence}"
