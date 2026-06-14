from fastapi import APIRouter

from backend.app.schemas.study import CourseCreate, CourseResponse
from backend.app.services import study_service

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=list[CourseResponse])
def list_courses() -> list:
    return study_service.list_courses()


@router.post("", response_model=CourseResponse, status_code=201)
def create_course(payload: CourseCreate):
    return study_service.create_course(payload)
