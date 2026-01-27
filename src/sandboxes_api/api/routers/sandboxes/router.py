import uuid

from fastapi import APIRouter

from .models import RunSandboxBody, RunSandboxResponse


router = APIRouter(
    tags=["Sandbox Lifecycle"],
)


@router.post(
    "",
    response_model=RunSandboxResponse,
    status_code=201,
)
async def run_sandbox(body: RunSandboxBody):
    # TODO: Implement sandbox creation logic
    return RunSandboxResponse(sandbox_id=str(uuid.uuid4()))


@router.delete(
    "/{sandbox_id}",
    status_code=204,
)
async def delete_sandbox(sandbox_id: str):
    # TODO: Implement sandbox deletion logic
    return
