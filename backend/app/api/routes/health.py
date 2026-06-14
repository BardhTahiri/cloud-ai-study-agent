from fastapi import APIRouter

from backend.app.core.config import settings
from backend.app.schemas.study import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service=settings.app_name)
