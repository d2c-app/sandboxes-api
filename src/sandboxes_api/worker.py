import logging
import sys

from rq import Worker

from sandboxes_api.config import settings
from sandboxes_api.infra.queue import QueueManager, SANDBOX_LIFECYCLE_QUEUE


_logger = logging.getLogger(__name__)


def main() -> None:
    """Main entry point for RQ worker."""

    QueueManager.init(settings().RQ_REDIS_URL)

    queue = QueueManager.sandbox_lifecycle

    _logger.info("Starting RQ worker for queue: %s", SANDBOX_LIFECYCLE_QUEUE)

    worker = Worker([queue], name=f"worker-{SANDBOX_LIFECYCLE_QUEUE}")

    try:
        worker.work()
    except KeyboardInterrupt:
        _logger.info("Worker interrupted by user")
        sys.exit(0)
    except Exception as e:
        _logger.error("Worker error: %s: %s", type(e).__name__, str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
