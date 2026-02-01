import logging

from sandboxes_api.config import settings
from sandboxes_api.api import run_api
from sandboxes_api.infra.queue import QueueManager


_logger = logging.getLogger(__name__)


def _setup_infra() -> None:
    QueueManager.init(settings().RQ_REDIS_URL)


def main() -> None:
    _setup_infra()
    run_api(host=settings().APP_HOST, port=settings().APP_PORT)


if __name__ == "__main__":
    main()
