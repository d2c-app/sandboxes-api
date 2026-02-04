from fastapi import APIRouter

from .models import HealthResponse


router = APIRouter(
    tags=["Miscellaneous"],
)


@router.get(
    "/healthz",
    response_model=HealthResponse,
)
def health_check():
    return HealthResponse()