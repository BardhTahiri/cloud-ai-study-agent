from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.study import StudyTaskCreate, StudyTaskResponse
from backend.app.services import study_service
from backend.app.services.file_service import extract_text_from_upload

router = APIRouter(prefix="/study-tasks", tags=["study tasks"])


@router.get("", response_model=list[StudyTaskResponse])
def list_tasks(db: Session = Depends(get_db)) -> list:
    return study_service.list_tasks(db)


@router.get("/{task_id}", response_model=StudyTaskResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    return study_service.get_task(db, task_id)


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: str, db: Session = Depends(get_db)) -> None:
    study_service.delete_task(db, task_id)


@router.post("", response_model=StudyTaskResponse, status_code=202)
def create_task(
    payload: StudyTaskCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    task = study_service.create_study_task(db, payload)
    background_tasks.add_task(study_service.run_study_task, task.id)
    return task


@router.post("/upload", response_model=StudyTaskResponse, status_code=202)
async def create_task_from_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    prompt: str = Form(default=""),
    course_id: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    text = await extract_text_from_upload(file)
    try:
        payload = StudyTaskCreate(
            title=title,
            course_id=course_id,
            prompt=prompt,
            material_text=text,
            source_type="pdf" if (file.filename or "").lower().endswith(".pdf") else "text",
            source_name=file.filename,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc

    task = study_service.create_study_task(db, payload)
    background_tasks.add_task(study_service.run_study_task, task.id)
    return task
