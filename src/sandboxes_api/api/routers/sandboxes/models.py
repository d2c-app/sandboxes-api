from pydantic import BaseModel, Field

from sandboxes_api.services.sandboxes import SandboxStatus, SandboxType


class RunSandboxBody(BaseModel):
    sandbox_type: SandboxType = Field(..., description="The type of sandbox to run")
    callback_url: str | None = Field(
        None,
        description="Optional callback URL to receive sandbox creation notification",
    )
    callback_verification: str | None = Field(
        None,
        max_length=256,
        description="Optional verification string included in the callback body so the receiver can authenticate the source",
    )


class RunSandboxResponse(BaseModel):
    sandbox_id: str = Field(..., description="The ID of the sandbox")
    status: SandboxStatus = Field(
        SandboxStatus.PENDING, description="The status of the sandbox"
    )


class DeleteSandboxResponse(BaseModel):
    sandbox_id: str = Field(..., description="The ID of the deleted sandbox")
