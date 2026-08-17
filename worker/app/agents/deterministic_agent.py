from __future__ import annotations

from math import ceil

from worker.app.agents.contracts import QuizQuestion, StudyInput, StudyPackage, StudyPlanDay
from worker.app.processors.text_processor import extract_topics, normalize_text, select_key_sentences


def generate_deterministic_package(study_input: StudyInput) -> StudyPackage:
    material = normalize_text(study_input.material_text)
    if len(material) < 30:
        raise ValueError("Material is too short to generate a study package.")

    topics = extract_topics(f"{study_input.prompt} {material}", limit=8)
    summary = select_key_sentences(material, topics, study_input.prompt, limit=5)
    quiz = _generate_quiz(topics, summary)
    study_plan = _generate_study_plan(topics, summary)

    return StudyPackage(
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
        options = _build_quiz_options(topic, answer, index)
        questions.append(
            QuizQuestion(
                question=f"{index}. Which option best explains '{topic}' based on the material?",
                answer=answer,
                topic=topic,
                options=options,
                correct_option=answer,
            )
        )

    if not questions:
        questions.append(
            QuizQuestion(
                question="1. What is the main idea of this material?",
                answer=fallback_answer,
                topic="Main Idea",
                options=_build_quiz_options("Main Idea", fallback_answer, 1),
                correct_option=fallback_answer,
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


def _build_quiz_options(topic: str, answer: str, index: int) -> list[str]:
    distractors = [
        f"{topic} is not connected to the uploaded material and can be skipped.",
        f"{topic} only matters for visual design and not for understanding the lesson.",
        f"{topic} is mainly about memorizing words without applying the concept.",
    ]
    options = [answer, *distractors]
    shift = index % len(options)
    return options[shift:] + options[:shift]


def _review_task(day_index: int, summary: list[str]) -> str:
    if not summary:
        return "Create one example that connects the topic to a real academic problem."

    sentence = summary[min(day_index, len(summary) - 1)]
    return f"Review this key point: {sentence}"
