import logging
from enum import StrEnum
from dataclasses import dataclass
import os

from sandboxes_api.config import settings
from sandboxes_api.infra.queue import QueueManager
from sandboxes_api.services.jobs import create_sandbox_job, delete_sandbox_job

# Initialize QueueManager on module import
QueueManager.initialize(settings().RQ_REDIS_URL)


_logger = logging.getLogger(__name__)


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

    # Map sandbox type to template type and ports
    template = "python-sandbox"
    expose_ports = [5432]

    _logger.info(
        "Enqueueing sandbox creation job: sandbox_id=%s, sandbox_type=%s",
        sandbox_id,
        sandbox_type,
    )

    queue = QueueManager.sandbox_lifecycle
    queue.enqueue(create_sandbox_job, sandbox_id, template, expose_ports)

    return Sandbox(
        id=sandbox_id, sandbox_type=sandbox_type, status=SandboxStatus.PENDING
    )


def delete_sandbox(sandbox_id: str) -> str:
    _logger.info("Enqueueing sandbox deletion job: sandbox_id=%s", sandbox_id)

    queue = QueueManager.sandbox_lifecycle
    queue.enqueue(delete_sandbox_job, sandbox_id)

    return sandbox_id
