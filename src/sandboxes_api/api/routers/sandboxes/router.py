from fastapi import APIRouter, Depends

from sandboxes_api.api.dependencies.auth import verify_auth_key
from sandboxes_api.services.sandboxes import create_sandbox, delete_sandbox

from .models import RunSandboxBody, RunSandboxResponse, DeleteSandboxResponse


router = APIRouter(
    tags=["Sandbox Lifecycle"],
    dependencies=[Depends(verify_auth_key)],
)


@router.post(
    "",
    response_model=RunSandboxResponse,
    status_code=201,
)
def run_sandbox_request(body: RunSandboxBody):
    sandbox = create_sandbox(body.sandbox_type)
    return RunSandboxResponse(sandbox_id=sandbox.id, status=sandbox.status)


@router.delete(
    "/{sandbox_id}",
    response_model=DeleteSandboxResponse,
)
def delete_sandbox_request(sandbox_id: str):
    # TODO: Should return 404 on non-existent sandbox

    # Strip whitespace to prevent issues with trailing spaces
    sandbox_id = sandbox_id.strip()
    deleted_sandbox_id = delete_sandbox(sandbox_id)
    return DeleteSandboxResponse(sandbox_id=deleted_sandbox_id)
