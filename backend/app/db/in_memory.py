from __future__ import annotations

from threading import Lock

from backend.app.models.entities import Course, StudyTask


class InMemoryStore:
    """Small development store used before PostgreSQL is added."""

    def __init__(self) -> None:
        self._courses: dict[str, Course] = {}
        self._tasks: dict[str, StudyTask] = {}
        self._lock = Lock()
        self._seed()

    def _seed(self) -> None:
        course = Course.create(
            name="Cloud Computing",
            description="Demo course for the AI study agent workflow.",
        )
        self._courses[course.id] = course

    def list_courses(self) -> list[Course]:
        with self._lock:
            return sorted(self._courses.values(), key=lambda course: course.created_at)

    def create_course(self, name: str, description: str = "") -> Course:
        with self._lock:
            course = Course.create(name=name, description=description)
            self._courses[course.id] = course
            return course

    def get_course(self, course_id: str) -> Course | None:
        with self._lock:
            return self._courses.get(course_id)

    def create_task(self, task: StudyTask) -> StudyTask:
        with self._lock:
            self._tasks[task.id] = task
            return task

    def save_task(self, task: StudyTask) -> StudyTask:
        with self._lock:
            self._tasks[task.id] = task
            return task

    def get_task(self, task_id: str) -> StudyTask | None:
        with self._lock:
            return self._tasks.get(task_id)

    def list_tasks(self) -> list[StudyTask]:
        with self._lock:
            return sorted(self._tasks.values(), key=lambda task: task.created_at, reverse=True)


store = InMemoryStore()
