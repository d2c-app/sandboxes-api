import logging

from sandboxes_api.config import settings
from sandboxes_api.api import run_api
from sandboxes_api.infra.agent_sandbox import AgentSandbox
from sandboxes_api.shared.singleton import Singleton


_logger = logging.getLogger(__name__)


def setup_infra() -> None:
    Singleton.set(AgentSandbox, AgentSandbox())


def main() -> None:
    setup_infra()
    run_api(host=settings().APP_HOST, port=settings().APP_PORT)


if __name__ == "__main__":
    main()
