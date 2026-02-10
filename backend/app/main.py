"""
myHealth API - FastAPI Application Entry Point

This module initializes and configures the FastAPI application with all
necessary middleware, routers, and exception handlers.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app.api.v1.router import api_router
from app.config import get_settings
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    generic_exception_handler,
    http_exception_handler,
)
from app.core.logging_config import get_logger, setup_logging
from app.middleware.cors import setup_cors
from app.middleware.logging_middleware import setup_logging_middleware
from app.middleware.rate_limit import setup_rate_limiting

# Get settings
settings = get_settings()

# Setup logging
logger = setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    app_name="myhealth",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.

    Handles startup and shutdown events for the application.
    """
    # Startup
    logger.info(
        f"Starting {settings.app_name} API",
        extra={
            "environment": settings.app_env,
            "debug": settings.debug,
        },
    )
    logger.info(f"API documentation available at /docs")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.app_name} API")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Health tracking application API with user authentication",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan,
)

# Setup middleware (order matters - last added is executed first)
setup_logging_middleware(app)
setup_cors(app, settings)
setup_rate_limiting(app, settings)

# Register exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include API router
app.include_router(api_router, prefix="/api/v1")


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """
    Root endpoint - redirects to API documentation.
    """
    return {
        "message": f"Welcome to {settings.app_name} API",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


# For running with uvicorn directly
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
