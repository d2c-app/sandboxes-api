from fastapi import Header, HTTPException, status

from sandboxes_api.config import settings


def verify_auth_key(x_api_key: str = Header(..., alias="X-API-Key")) -> None:
    if x_api_key != settings().AUTH_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication key",
        )
