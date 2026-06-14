from __future__ import annotations

from fastapi import HTTPException, status

from backend.app.db.in_memory import store
from backend.app.models.entities import StudyTask
from backend.app.schemas.study import CourseCreate, StudyTaskCreate
from worker.app.agents.study_agent import StudyInput, generate_study_package


def create_course(payload: CourseCreate):
    return store.create_course(name=payload.name, description=payload.description)


def list_courses():
    return store.list_courses()


def list_tasks():
    return store.list_tasks()


def get_task(task_id: str):
    task = store.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


def create_study_task(payload: StudyTaskCreate) -> StudyTask:
    if payload.course_id and store.get_course(payload.course_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    task = StudyTask.create(
        title=payload.title,
        course_id=payload.course_id,
        prompt=payload.prompt,
        source_type=payload.source_type,
        source_name=payload.source_name,
        material_text=payload.material_text,
    )
    store.create_task(task)

    task.mark_processing()
    store.save_task(task)

    try:
        result = generate_study_package(
            StudyInput(
                title=payload.title,
                prompt=payload.prompt,
                material_text=payload.material_text,
            )
        )
        task.mark_completed(result.to_dict())
    except Exception as exc:
        task.mark_failed(str(exc))

    return store.save_task(task)
