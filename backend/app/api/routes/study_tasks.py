from fastapi import APIRouter, File, Form, UploadFile

from backend.app.schemas.study import StudyTaskCreate, StudyTaskResponse
from backend.app.services import study_service
from backend.app.services.file_service import extract_text_from_upload

router = APIRouter(prefix="/study-tasks", tags=["study tasks"])


@router.get("", response_model=list[StudyTaskResponse])
def list_tasks() -> list:
    return study_service.list_tasks()


@router.get("/{task_id}", response_model=StudyTaskResponse)
def get_task(task_id: str):
    return study_service.get_task(task_id)


@router.post("", response_model=StudyTaskResponse, status_code=201)
def create_task(payload: StudyTaskCreate):
    return study_service.create_study_task(payload)


@router.post("/upload", response_model=StudyTaskResponse, status_code=201)
async def create_task_from_upload(
    file: UploadFile = File(...),
    title: str = Form(...),
    prompt: str = Form(default=""),
    course_id: str | None = Form(default=None),
):
    text = await extract_text_from_upload(file)
    payload = StudyTaskCreate(
        title=title,
        course_id=course_id,
        prompt=prompt,
        material_text=text,
        source_type="pdf" if (file.filename or "").lower().endswith(".pdf") else "text",
        source_name=file.filename,
    )
    return study_service.create_study_task(payload)
