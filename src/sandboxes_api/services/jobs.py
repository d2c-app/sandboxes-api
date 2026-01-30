import logging

from sandboxes_api.infra.agent_sandbox import AgentSandbox


_logger = logging.getLogger(__name__)


def create_sandbox_job(sandbox_id: str, template: str, expose_ports: list[int]) -> None:
    """
    Background job to create a sandbox.

    Args:
        sandbox_id: Unique identifier for the sandbox
        template: Template name for the sandbox
        expose_ports: List of ports to expose
    """
    _logger.info(
        "Starting sandbox creation: sandbox_id=%s, template=%s", sandbox_id, template
    )

    try:
        sandbox_claim = AgentSandbox().claim_sandbox(sandbox_id, template, expose_ports)

        _logger.info(
            "Sandbox created successfully: sandbox_id=%s, hostname=%s, template=%s",
            sandbox_id,
            sandbox_claim.hostname,
            sandbox_claim.template,
        )

        # TODO: Prepare sandbox for use
        _logger.debug("Sandbox preparation completed: sandbox_id=%s", sandbox_id)

    except Exception as e:
        _logger.error(
            "Sandbox creation failed: sandbox_id=%s, template=%s, error=%s: %s",
            sandbox_id,
            template,
            type(e).__name__,
            str(e),
            exc_info=True,
        )
        raise


def delete_sandbox_job(sandbox_id: str) -> None:
    """
    Background job to delete a sandbox.

    Args:
        sandbox_id: Unique identifier for the sandbox to delete
    """
    _logger.info("Starting sandbox deletion: sandbox_id=%s", sandbox_id)

    try:
        AgentSandbox().release_sandbox(sandbox_id)
        _logger.info("Sandbox deleted successfully: sandbox_id=%s", sandbox_id)

    except Exception as e:
        _logger.error(
            "Sandbox deletion failed: sandbox_id=%s, error=%s: %s",
            sandbox_id,
            type(e).__name__,
            str(e),
            exc_info=True,
        )
        raise
