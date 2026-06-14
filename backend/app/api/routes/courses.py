from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.study import CourseCreate, CourseResponse
from backend.app.services import study_service

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=list[CourseResponse])
def list_courses(db: Session = Depends(get_db)) -> list:
    return study_service.list_courses(db)


@router.post("", response_model=CourseResponse, status_code=201)
def create_course(payload: CourseCreate, db: Session = Depends(get_db)):
    return study_service.create_course(db, payload)
