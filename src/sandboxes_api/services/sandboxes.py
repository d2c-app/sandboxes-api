from enum import StrEnum
from dataclasses import dataclass
import os


class SandboxType(StrEnum):
    POSTGRES = "postgres"


class SandboxStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Sandbox:
    id: str
    sandbox_type: SandboxType
    status: SandboxStatus


def create_sandbox(sandbox_type: SandboxType) -> Sandbox:
    sandbox_id = f"sb-{os.urandom(4).hex()}"

    # TODO: Offload sandbox creation to a background task (use RQ worker or Celery)

    return Sandbox(
        id=sandbox_id, sandbox_type=sandbox_type, status=SandboxStatus.PENDING
    )


def delete_sandbox(sandbox_id: str) -> str:
    # TODO: Offload sandbox deletion to a background task
    return sandbox_id
