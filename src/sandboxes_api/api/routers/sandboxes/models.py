from pydantic import BaseModel, Field

from sandboxes_api.services.sandboxes import SandboxStatus, SandboxType


class RunSandboxBody(BaseModel):
    sandbox_type: SandboxType = Field(..., description="The type of sandbox to run")
    callback_url: str | None = Field(
        None,
        description="Optional callback URL to receive sandbox creation notification",
    )


class RunSandboxResponse(BaseModel):
    sandbox_id: str = Field(..., description="The ID of the sandbox")
    status: SandboxStatus = Field(
        SandboxStatus.PENDING, description="The status of the sandbox"
    )


class DeleteSandboxResponse(BaseModel):
    sandbox_id: str = Field(..., description="The ID of the deleted sandbox")
