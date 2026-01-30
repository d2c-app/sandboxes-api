import logging
from typing import Optional

import redis
from rq import Queue


_logger = logging.getLogger(__name__)

# Queue name constant
SANDBOX_LIFECYCLE_QUEUE = "sandbox_lifecycle"


class QueueManager:
    """Manages RQ queues with static queue instances."""

    _connection: Optional[redis.Redis] = None
    sandbox_lifecycle: Optional[Queue] = None

    @classmethod
    def initialize(cls, redis_url: str) -> None:
        """
        Initialize QueueManager with Redis connection and create static queues.

        Args:
            redis_url: Redis connection URL
        """
        if cls._connection is None:
            _logger.debug("Initializing QueueManager with Redis: %s", redis_url)
            cls._connection = redis.from_url(redis_url)
            cls._connection.ping()  # Test the connection
            cls.sandbox_lifecycle = Queue(
                SANDBOX_LIFECYCLE_QUEUE, connection=cls._connection
            )
            _logger.debug("Created static queue: %s", SANDBOX_LIFECYCLE_QUEUE)
