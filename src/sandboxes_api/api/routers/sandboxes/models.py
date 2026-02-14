from pydantic import BaseModel, Field

from sandboxes_api.services.sandboxes import SandboxStatus, SandboxType


class RunSandboxBody(BaseModel):
    sandbox_type: SandboxType = Field(..., description="The type of sandbox to run")
    ttl_seconds: int | None = Field(
        None,
        gt=0,
        description="Optional time-to-live in seconds for the sandbox. When set, the sandbox will be automatically shut down after this duration (counted from sandbox creation, not request time). A 10-second grace period is added internally.",
    )
    callback_url: str | None = Field(
        None,
        description="Optional callback URL to receive sandbox creation notification",
    )
    callback_secret: str | None = Field(
        None,
        max_length=256,
        description="Secret used to sign callback payloads with HMAC-SHA256 (required when callback_url is provided)",
    )


class RunSandboxResponse(BaseModel):
    sandbox_id: str = Field(..., description="The ID of the sandbox")
    sandbox_type: SandboxType = Field(..., description="The type of sandbox")
    status: SandboxStatus = Field(
        SandboxStatus.PENDING, description="The status of the sandbox"
    )


class DeleteSandboxResponse(BaseModel):
    sandbox_id: str = Field(..., description="The ID of the deleted sandbox")
