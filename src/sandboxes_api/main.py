import logging

from sandboxes_api.config import settings
from sandboxes_api.api import run_api


_logger = logging.getLogger(__name__)


def main() -> None:
    run_api(host=settings().APP_HOST, port=settings().APP_PORT)


if __name__ == "__main__":
    main()
