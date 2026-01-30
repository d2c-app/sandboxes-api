from typing import Literal

from pydantic import BaseModel, Field

from sandboxes_api.services.sandboxes import SandboxStatus


class RunSandboxBody(BaseModel):
    sandbox_type: Literal["postgres",] = Field(
        ..., description="The type of sandbox to run"
    )


class RunSandboxResponse(BaseModel):
    sandbox_id: str = Field(..., description="The ID of the sandbox")
    status: SandboxStatus = Field(
        SandboxStatus.PENDING, description="The status of the sandbox"
    )


class DeleteSandboxResponse(BaseModel):
    sandbox_id: str = Field(..., description="The ID of the deleted sandbox")
