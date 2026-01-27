from typing import Literal

from pydantic import BaseModel, Field


class RunSandboxBody(BaseModel):
    sandbox_type: Literal["postgres",] = Field(
        ..., description="The type of sandbox to run"
    )


class RunSandboxResponse(BaseModel):
    sandbox_id: str = Field(..., description="The ID of the sandbox")
    status: Literal["pending", "running", "completed", "failed"] = Field(
        "pending", description="The status of the sandbox"
    )
