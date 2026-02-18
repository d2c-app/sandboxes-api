from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from sandboxes_api.config import settings

_api_key_header = APIKeyHeader(name="X-API-Key")


def verify_auth_key(x_api_key: str = Depends(_api_key_header)) -> None:
    if x_api_key != settings().AUTH_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication key",
        )
