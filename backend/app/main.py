"""FastAPI entry point for the AURA local backend."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.chat import router as chat_router
from app.config import Settings, get_settings
from app.database.connection import initialize_database
from app.models.schemas import HealthResponse
from app.services.llm_service import LLMService


logger = logging.getLogger("aura.backend")


def configure_logging(level: str) -> None:
    """Configure a concise process-wide log format once at startup."""

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def create_app(
    settings: Settings | None = None,
    llm_service: LLMService | None = None,
) -> FastAPI:
    """Build an application instance, allowing isolated test settings."""

    runtime_settings = settings or get_settings()
    configure_logging(runtime_settings.log_level)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        initialize_database(runtime_settings.database_path)
        logger.info("AURA backend started", extra={"version": runtime_settings.app_version})
        yield
        logger.info("AURA backend stopped")

    app = FastAPI(
        title=runtime_settings.app_name,
        version=runtime_settings.app_version,
        lifespan=lifespan,
    )
    app.state.settings = runtime_settings
    app.state.llm_service = llm_service or LLMService(runtime_settings)

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("Unhandled request error", extra={"request_id": request_id})
            raise
        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", str(uuid4()))
        logger.exception("Unhandled application exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id},
            headers={"X-Request-ID": request_id},
        )

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    async def health(request: Request) -> HealthResponse:
        return HealthResponse(
            status="ok",
            service=runtime_settings.app_name,
            version=runtime_settings.app_version,
            request_id=request.state.request_id,
        )

    app.include_router(chat_router)
    return app


app = create_app()
