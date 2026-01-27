import logging

from sandboxes_api.config import settings


def main() -> None:
    logging.info(
        f"Sandboxes API running on {settings().APP_HOST}:{settings().APP_PORT}"
    )


if __name__ == "__main__":
    main()
