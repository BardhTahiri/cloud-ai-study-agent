from __future__ import annotations

import re
from collections import Counter


STOPWORDS = {
    "about",
    "after",
    "also",
    "and",
    "are",
    "because",
    "between",
    "can",
    "for",
    "from",
    "has",
    "have",
    "into",
    "its",
    "more",
    "not",
    "that",
    "the",
    "their",
    "then",
    "there",
    "these",
    "this",
    "through",
    "using",
    "when",
    "where",
    "with",
    "will",
    "you",
    "your",
}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def split_sentences(text: str) -> list[str]:
    normalized = normalize_text(text)
    if not normalized:
        return []

    parts = re.split(r"(?<=[.!?])\s+", normalized)
    return [part.strip() for part in parts if len(part.strip()) > 20]


def tokenize(text: str) -> list[str]:
    words = re.findall(r"\b[\w-]{3,}\b", text.lower())
    return [word.strip("-") for word in words if word.strip("-") and word not in STOPWORDS]


def extract_topics(text: str, limit: int = 8) -> list[str]:
    words = tokenize(text)
    counts = Counter(words)
    topics = [word for word, _ in counts.most_common(limit)]
    return [topic.replace("-", " ").title() for topic in topics]


def sentence_score(sentence: str, topics: list[str], prompt: str = "") -> int:
    lower_sentence = sentence.lower()
    score = sum(3 for topic in topics if topic.lower() in lower_sentence)

    for prompt_word in tokenize(prompt):
        if prompt_word in lower_sentence:
            score += 2

    return score + min(len(sentence) // 80, 3)


def select_key_sentences(text: str, topics: list[str], prompt: str = "", limit: int = 5) -> list[str]:
    sentences = split_sentences(text)
    if not sentences:
        return [normalize_text(text)[:500]] if text.strip() else []

    ranked = sorted(
        enumerate(sentences),
        key=lambda item: sentence_score(item[1], topics, prompt),
        reverse=True,
    )
    selected_indexes = sorted(index for index, _ in ranked[:limit])
    return [sentences[index] for index in selected_indexes]
