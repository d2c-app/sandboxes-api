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
    """
    Service health check.

    Returns the current operational status of the API service.
    Used by orchestration systems to verify service availability.
    """
    return HealthResponse()
