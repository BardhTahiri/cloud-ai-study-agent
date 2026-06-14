from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models import CourseRecord, StudyTaskRecord
from backend.app.db.session import SessionLocal
from backend.app.models.entities import TaskStatus, utc_now
from backend.app.schemas.study import CourseCreate, StudyTaskCreate
from worker.app.agents.study_agent import StudyInput, generate_study_package
from uuid import uuid4


def create_course(db: Session, payload: CourseCreate):
    course = CourseRecord(
        id=str(uuid4()),
        name=payload.name,
        description=payload.description,
        created_at=utc_now(),
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def list_courses(db: Session):
    return db.execute(select(CourseRecord).order_by(CourseRecord.created_at)).scalars().all()


def list_tasks(db: Session):
    return db.execute(select(StudyTaskRecord).order_by(StudyTaskRecord.created_at.desc())).scalars().all()


def get_task(db: Session, task_id: str):
    task = db.get(StudyTaskRecord, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


def delete_task(db: Session, task_id: str) -> None:
    task = db.get(StudyTaskRecord, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    db.delete(task)
    db.commit()


def create_study_task(db: Session, payload: StudyTaskCreate) -> StudyTaskRecord:
    if payload.course_id and db.get(CourseRecord, payload.course_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    task = StudyTaskRecord(
        id=str(uuid4()),
        title=payload.title,
        course_id=payload.course_id,
        prompt=payload.prompt,
        source_type=payload.source_type,
        source_name=payload.source_name,
        material_text=payload.material_text,
        status=TaskStatus.pending.value,
        progress=0,
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def run_study_task(task_id: str) -> None:
    with SessionLocal() as db:
        task = db.get(StudyTaskRecord, task_id)
        if task is None:
            return

        _mark_processing(task)
        db.commit()

        title = task.title
        prompt = task.prompt
        material_text = task.material_text

    result: dict | None = None
    error: str | None = None
    try:
        result = generate_study_package(
            StudyInput(
                title=title,
                prompt=prompt,
                material_text=material_text,
            )
        ).to_dict()
    except Exception as exc:
        error = str(exc)

    with SessionLocal() as db:
        task = db.get(StudyTaskRecord, task_id)
        if task is None:
            return
        if error:
            _mark_failed(task, error)
        else:
            _mark_completed(task, result or {})
        db.commit()


def _mark_processing(task: StudyTaskRecord) -> None:
    task.status = TaskStatus.processing.value
    task.progress = 35
    task.updated_at = utc_now()


def _mark_completed(task: StudyTaskRecord, result: dict) -> None:
    task.status = TaskStatus.completed.value
    task.progress = 100
    task.result = result
    task.error = None
    task.updated_at = utc_now()


def _mark_failed(task: StudyTaskRecord, error: str) -> None:
    task.status = TaskStatus.failed.value
    task.progress = 100
    task.error = error
    task.updated_at = utc_now()
