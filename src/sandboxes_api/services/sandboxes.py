from enum import StrEnum
from dataclasses import dataclass
import os

from sandboxes_api.shared.singleton import Singleton
from sandboxes_api.infra.agent_sandbox import AgentSandbox


class SandboxType(StrEnum):
    POSTGRES = "postgres"


class SandboxStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    FAILED = "failed"


@dataclass(frozen=True)
class Sandbox:
    id: str
    sandbox_type: SandboxType
    status: SandboxStatus


def create_sandbox(sandbox_type: SandboxType) -> Sandbox:
    sandbox_id = f"sb-{os.urandom(4).hex()}"

    # TODO: Offload sandbox creation to a background task (use RQ worker or Celery)
    _create_sandbox(sandbox_id, sandbox_type)

    return Sandbox(
        id=sandbox_id, sandbox_type=sandbox_type, status=SandboxStatus.PENDING
    )


def delete_sandbox(sandbox_id: str) -> str:
    # TODO: Offload sandbox deletion to a background task
    _delete_sandbox(sandbox_id)

    return sandbox_id


def _create_sandbox(sandbox_id: str, sandbox_type: SandboxType) -> None:
    # TODO: Map sandbox type to template type and ports
    template = "python-sandbox"
    expose_ports = [5432]

    if not (agent_sandbox := Singleton.get(AgentSandbox)):
        raise RuntimeError("Sandbox provider AgentSandbox is not initialized")

    sandbox_claim = agent_sandbox.claim_sandbox(sandbox_id, template, expose_ports)

    # TODO: Prepare sandbox for use
    pass


def _delete_sandbox(sandbox_id: str) -> None:
    if not (agent_sandbox := Singleton.get(AgentSandbox)):
        raise RuntimeError("Sandbox provider AgentSandbox is not initialized")

    agent_sandbox.release_sandbox(sandbox_id)
    return sandbox_id
