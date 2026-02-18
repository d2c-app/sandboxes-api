import logging
import time
from enum import StrEnum
from dataclasses import dataclass
import os
import secrets
import hashlib
import hmac
import json

import httpx
import redis as redis_lib
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from sandboxes_api.infra.queue import QueueManager
from sandboxes_api.infra.agent_sandbox import AgentSandbox


_logger = logging.getLogger(__name__)


class SandboxType(StrEnum):
    POSTGRES = "postgres"
    REDIS = "redis"


_TYPE_TO_TEMPLATE = {
    SandboxType.POSTGRES: "postgres-16-alpine-template",
    SandboxType.REDIS: "redis-7-alpine-template",
}


class SandboxStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    FAILED = "failed"


@dataclass(frozen=True)
class Sandbox:
    id: str
    sandbox_type: SandboxType
    status: SandboxStatus


@dataclass(frozen=True)
class DatabaseCredentials:
    username: str
    password: str
    hostname: str
    port: int = 5432
    database: str = "postgres"


@dataclass(frozen=True)
class RedisCredentials:
    username: str
    password: str
    hostname: str
    port: int = 6379


def create_sandbox(
    sandbox_type: SandboxType,
    ttl_seconds: int | None = None,
    callback_url: str | None = None,
    callback_secret: str | None = None,
) -> Sandbox:
    sandbox_id = f"sb-{os.urandom(4).hex()}"

    if not (template := _TYPE_TO_TEMPLATE.get(sandbox_type)):
        raise ValueError(f"Invalid sandbox type: {sandbox_type}")

    _logger.info(
        "Enqueueing sandbox creation job: sandbox_id=%s, sandbox_type=%s, ttl_seconds=%s, callback_url=%s",
        sandbox_id,
        sandbox_type,
        ttl_seconds,
        callback_url,
    )

    queue = QueueManager.sandbox_lifecycle
    queue.enqueue(
        _create_sandbox_job,
        sandbox_id,
        sandbox_type,
        ttl_seconds,
        callback_url,
        callback_secret,
    )

    return Sandbox(
        id=sandbox_id, sandbox_type=sandbox_type, status=SandboxStatus.PENDING
    )


def delete_sandbox(sandbox_id: str) -> str:
    _logger.info("Enqueueing sandbox deletion job: sandbox_id=%s", sandbox_id)

    queue = QueueManager.sandbox_lifecycle
    queue.enqueue(_delete_sandbox_job, sandbox_id)

    return sandbox_id


def _create_sandbox_job(
    sandbox_id: str,
    sandbox_type: SandboxType,
    ttl_seconds: int | None = None,
    callback_url: str | None = None,
    callback_secret: str | None = None,
) -> None:
    """
    Background job to create a sandbox.

    Args:
        sandbox_id: Unique identifier for the sandbox
        sandbox_type: Type of the sandbox
        ttl_seconds: Optional time-to-live in seconds; shutdown time is computed at claim creation
        callback_url: Optional URL to receive sandbox creation notification
        callback_secret: Optional secret used to sign callbacks with HMAC-SHA256
    """
    if not (template := _TYPE_TO_TEMPLATE.get(sandbox_type)):
        raise ValueError(f"Invalid sandbox type: {sandbox_type}")

    _logger.info(
        "Starting sandbox creation: sandbox_id=%s, sandbox_type=%s, ttl_seconds=%s, callback_url=%s",
        sandbox_id,
        sandbox_type,
        ttl_seconds,
        callback_url,
    )

    credentials: DatabaseCredentials | RedisCredentials | None = None
    status = SandboxStatus.FAILED

    try:
        sandbox_claim = AgentSandbox().claim_sandbox(
            sandbox_id, template, ttl_seconds=ttl_seconds
        )

        _logger.info(
            "Sandbox created successfully: sandbox_id=%s, hostname=%s, template=%s",
            sandbox_id,
            sandbox_claim.hostname,
            sandbox_claim.template,
        )

        credentials = _prepare_sandbox(sandbox_type, sandbox_claim.hostname, sandbox_id)
        if credentials:
            _logger.info(
                "Sandbox preparation completed: sandbox_id=%s, credentials_username=%s",
                sandbox_id,
                credentials.username,
            )
            status = SandboxStatus.RUNNING

    except Exception as e:
        _logger.error(
            "Sandbox creation failed: sandbox_id=%s, sandbox_type=%s, error=%s: %s",
            sandbox_id,
            sandbox_type,
            type(e).__name__,
            str(e),
            exc_info=True,
        )
        raise
    finally:
        # Send callback if URL is provided
        if callback_url:
            _send_callback(
                callback_url,
                sandbox_id,
                sandbox_type,
                credentials,
                status=status,
                callback_secret=callback_secret,
            )


def _prepare_sandbox(
    sandbox_type: SandboxType, hostname: str, sandbox_id: str
) -> DatabaseCredentials | RedisCredentials:
    """
    Prepare a sandbox for use based on its type.

    Args:
        sandbox_type: Type of the sandbox
        hostname: Hostname of the sandbox
        sandbox_id: Unique identifier for the sandbox (used as database username)

    Returns:
        DatabaseCredentials
    """
    if sandbox_type == SandboxType.POSTGRES:
        username = sandbox_id
        password = secrets.token_urlsafe(16)

        # Hardcoded initial credentials - will be adjusted later
        # Use postgresql+psycopg:// to explicitly use psycopg3 driver
        initial_connection_string = (
            f"postgresql+psycopg://postgres:postgres@{hostname}:5432/postgres"
        )

        # Wait for PostgreSQL to be ready (pod might be Ready but PostgreSQL not accepting connections yet)
        max_retries = 10
        retry_delay = 2  # seconds
        engine = None

        for attempt in range(max_retries):
            try:
                engine = create_engine(
                    initial_connection_string, connect_args={"connect_timeout": 5}
                )
                # Test connection
                with engine.connect() as test_conn:
                    test_conn.execute(text("SELECT 1"))
                break  # Connection successful
            except OperationalError as e:
                if attempt < max_retries - 1:
                    _logger.debug(
                        "PostgreSQL not ready yet (attempt %d/%d): hostname=%s, waiting %ds...",
                        attempt + 1,
                        max_retries,
                        hostname,
                        retry_delay,
                    )
                    time.sleep(retry_delay)
                    retry_delay = min(
                        retry_delay * 1.5, 10
                    )  # Exponential backoff, max 10s
                else:
                    raise

        if engine is None:
            raise RuntimeError("Failed to create database engine after retries")

        try:
            with engine.begin() as conn:
                # Create superuser with generated credentials
                # PostgreSQL CREATE USER doesn't support parameterized queries,
                # so we need to embed the password directly. Escape single quotes by doubling them.
                escaped_password = password.replace("'", "''")
                create_user_query = text(
                    f"CREATE USER \"{username}\" WITH SUPERUSER PASSWORD '{escaped_password}'"
                )
                conn.execute(create_user_query)

            _logger.info(
                "Created PostgreSQL superuser: hostname=%s, username=%s, password=%s",  # Remove password from logging after debug
                hostname,
                username,
                password,
            )

            return DatabaseCredentials(
                username=username,
                password=password,
                hostname=hostname,
                port=5432,
                database="postgres",
            )
        except Exception as e:
            _logger.error(
                "Failed to prepare PostgreSQL sandbox: hostname=%s, error=%s: %s",
                hostname,
                type(e).__name__,
                str(e),
                exc_info=True,
            )
            raise

    if sandbox_type == SandboxType.REDIS:
        username = sandbox_id
        password = secrets.token_urlsafe(16)

        max_retries = 10
        retry_delay = 2  # seconds
        client = None

        for attempt in range(max_retries):
            try:
                client = redis_lib.Redis(
                    host=hostname, port=6379, socket_connect_timeout=5
                )
                client.ping()
                break
            except (redis_lib.ConnectionError, redis_lib.TimeoutError):
                if attempt < max_retries - 1:
                    _logger.debug(
                        "Redis not ready yet (attempt %d/%d): hostname=%s, waiting %ds...",
                        attempt + 1,
                        max_retries,
                        hostname,
                        retry_delay,
                    )
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 1.5, 10)
                else:
                    raise

        if client is None:
            raise RuntimeError("Failed to connect to Redis after retries")

        try:
            client.execute_command(
                "ACL",
                "SETUSER",
                username,
                "on",
                f">{password}",
                "~*",
                "&*",
                "+@all",
            )

            _logger.info(
                "Created Redis user: hostname=%s, username=%s, password=%s",
                hostname,
                username,
                password,
            )

            return RedisCredentials(
                username=username,
                password=password,
                hostname=hostname,
                port=6379,
            )
        except Exception as e:
            _logger.error(
                "Failed to prepare Redis sandbox: hostname=%s, error=%s: %s",
                hostname,
                type(e).__name__,
                str(e),
                exc_info=True,
            )
            raise
        finally:
            client.close()

    raise ValueError(f"Unknown sandbox type: {sandbox_type}")


def _send_callback(
    callback_url: str,
    sandbox_id: str,
    sandbox_type: SandboxType,
    credentials: DatabaseCredentials | RedisCredentials | None,
    status: SandboxStatus,
    callback_secret: str | None = None,
) -> None:
    """
    Send a POST request to the callback URL with sandbox information.

    Args:
        callback_url: URL to send the callback to
        sandbox_id: Unique identifier for the sandbox
        sandbox_type: Type of the sandbox
        credentials: Database credentials for the sandbox (None if status is FAILED)
        status: Status of the sandbox creation (SandboxStatus.RUNNING or SandboxStatus.FAILED)
        callback_secret: Optional secret used to sign callback payload with HMAC-SHA256
    """
    try:
        # Prepare callback payload based on sandbox type and status
        if status == SandboxStatus.RUNNING and credentials:
            if sandbox_type == SandboxType.POSTGRES:
                payload = {
                    "sandbox_id": sandbox_id,
                    "status": status.value,
                    "credentials": {
                        "user": credentials.username,
                        "password": credentials.password,
                    },
                }
            elif sandbox_type == SandboxType.REDIS:
                payload = {
                    "sandbox_id": sandbox_id,
                    "status": status.value,
                    "credentials": {
                        "user": credentials.username,
                        "password": credentials.password,
                    },
                }
            else:
                raise NotImplementedError(
                    f"Callback not implemented for sandbox type: {sandbox_type}"
                )
        else:
            # Failure case - no credentials
            payload = {
                "sandbox_id": sandbox_id,
                "status": status.value,
                "credentials": {},
            }

        body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode(
            "utf-8"
        )
        headers = {"Content-Type": "application/json"}

        if callback_secret:
            timestamp = str(int(time.time()))
            signed_payload = timestamp.encode("utf-8") + b"." + body
            signature = hmac.new(
                callback_secret.encode("utf-8"),
                signed_payload,
                hashlib.sha256,
            ).hexdigest()
            headers["X-Sandbox-Timestamp"] = timestamp
            headers["X-Sandbox-Signature"] = f"sha256={signature}"

        _logger.info(
            "Sending callback: callback_url=%s, sandbox_id=%s",
            callback_url,
            sandbox_id,
        )

        with httpx.Client(timeout=30.0) as client:
            response = client.post(callback_url, content=body, headers=headers)
            response.raise_for_status()

        _logger.info(
            "Callback sent successfully: callback_url=%s, sandbox_id=%s, status_code=%d",
            callback_url,
            sandbox_id,
            response.status_code,
        )

    except Exception as e:
        _logger.error(
            "Failed to send callback: callback_url=%s, sandbox_id=%s, error=%s: %s",
            callback_url,
            sandbox_id,
            type(e).__name__,
            str(e),
            exc_info=True,
        )
        # Don't raise - callback failure shouldn't fail sandbox creation


def _delete_sandbox_job(sandbox_id: str) -> None:
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
