from fastapi import FastAPI, APIRouter
import uvicorn

from .routers import sandboxes


def _get_fastapi() -> FastAPI:
    app = FastAPI(
        title="Sandboxes API",
        description="Microservice API for managing sandboxes lifecycle",
    )
    api_router = APIRouter()
    api_router.include_router(sandboxes.router, prefix="/sandboxes")

    app.include_router(api_router)

    return app


def run_api(host: str = "0.0.0.0", port: int = 8000) -> None:
    app = _get_fastapi()
    uvicorn.run(app, host=host, port=port)
