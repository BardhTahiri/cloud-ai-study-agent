from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TaskStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


@dataclass
class Course:
    id: str
    name: str
    description: str = ""
    created_at: datetime = field(default_factory=utc_now)

    @classmethod
    def create(cls, name: str, description: str = "") -> "Course":
        return cls(id=str(uuid4()), name=name, description=description)


@dataclass
class StudyTask:
    id: str
    title: str
    course_id: str | None
    prompt: str
    source_type: str
    source_name: str | None
    material_text: str
    status: TaskStatus = TaskStatus.pending
    progress: int = 0
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    @classmethod
    def create(
        cls,
        *,
        title: str,
        course_id: str | None,
        prompt: str,
        source_type: str,
        source_name: str | None,
        material_text: str,
    ) -> "StudyTask":
        return cls(
            id=str(uuid4()),
            title=title,
            course_id=course_id,
            prompt=prompt,
            source_type=source_type,
            source_name=source_name,
            material_text=material_text,
        )

    def mark_processing(self) -> None:
        self.status = TaskStatus.processing
        self.progress = 30
        self.updated_at = utc_now()

    def mark_completed(self, result: dict[str, Any]) -> None:
        self.status = TaskStatus.completed
        self.progress = 100
        self.result = result
        self.error = None
        self.updated_at = utc_now()

    def mark_failed(self, error: str) -> None:
        self.status = TaskStatus.failed
        self.progress = 100
        self.error = error
        self.updated_at = utc_now()
