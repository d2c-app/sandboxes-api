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
    """
    Create a new sandbox environment.

    This endpoint initiates the provisioning of a secure sandbox environment based on the specified type.
    The process is asynchronous; initial status is returned immediately.
    For extra security, a callback secret can be provided and will be used to sign callbacks with HMAC-SHA256.
    Signed callbacks include `X-Sandbox-Timestamp` and `X-Sandbox-Signature` headers.

    - **sandbox_type**: Type of the sandbox to create.
    - **callback_url**: (Optional) URL to receive status updates.
    - **callback_secret**: (Optional) Secret used to sign callback payloads with HMAC-SHA256. Max 256 characters.
    """
    sandbox = create_sandbox(
        body.sandbox_type,
        callback_url=body.callback_url,
        callback_secret=body.callback_secret,
    )
    return RunSandboxResponse(
        sandbox_id=sandbox.id, sandbox_type=sandbox.sandbox_type, status=sandbox.status
    )


@router.delete(
    "/{sandbox_id}",
    response_model=DeleteSandboxResponse,
)
def delete_sandbox_request(sandbox_id: str):
    """
    Terminate a sandbox instance.

    This endpoint requests the termination and deletion of an active sandbox identified by its ID.
    Resources associated with the sandbox will be released.

    - **sandbox_id**: Unique identifier of the sandbox to delete.
    """
    # Strip whitespace to prevent issues with trailing spaces
    sandbox_id = sandbox_id.strip()
    deleted_sandbox_id = delete_sandbox(sandbox_id)
    return DeleteSandboxResponse(sandbox_id=deleted_sandbox_id)
