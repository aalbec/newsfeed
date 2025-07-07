"""FastAPI application entry point for the IT Newsfeed API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from src.api.routers import ingest, retrieve
from src.ingestion import BackgroundIngestionService
from src.models.api import (
    BadRequestErrorResponse,
    DependencyHealth,
    HealthResponse,
    InternalServerErrorResponse,
    RootResponse,
    ValidationErrorResponse,
)
from src.registry import FilterRegistry, SourceRegistry
from src.storage import InMemoryStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown.

    This function manages the complete lifecycle of the FastAPI application,
    including initialization of core components and background services.

    Key Features:
    - Initializes storage, registries, and background ingestion service
    - Starts background ingestion for continuous news fetching
    - Ensures graceful shutdown of all services
    - Provides comprehensive logging for monitoring

    Potential Pitfalls Addressed:
    - Proper startup/shutdown sequence for background services
    - Error handling during initialization
    - Resource cleanup on shutdown
    - Integration with existing components
    """
    logger.info("🚀 Starting IT Newsfeed API...")

    # Initialize core components
    app.state.storage = InMemoryStore()
    app.state.source_registry = SourceRegistry()
    app.state.filter_registry = FilterRegistry()

    # Initialize background ingestion service
    # This implements the "continuously fetch IT-related news"
    app.state.background_ingestion = BackgroundIngestionService(
        storage=app.state.storage,
        source_registry=app.state.source_registry,
        filter_registry=app.state.filter_registry
    )

    # Register default sources for continuous ingestion
    # These sources will be automatically fetched in the background
    await _register_default_sources(app.state.source_registry)

    # Register default filters for content filtering
    # These filters will be applied to all ingested items
    await _register_default_filters(app.state.filter_registry)

    # Start background ingestion service
    try:
        await app.state.background_ingestion.start()
        logger.info("✅ Background ingestion service started")
    except Exception as e:
        logger.error(f"❌ Failed to start background ingestion: {e}")
        # Continue startup even if background ingestion fails
        # This ensures the API remains functional for manual ingestion

    logger.info("✅ Core components initialized")
    logger.info("🔍 API docs available at http://localhost:8000/docs")
    logger.info("🔍 Alternative docs at http://localhost:8000/redoc")

    yield

    # Shutdown background ingestion service
    try:
        if hasattr(app.state, 'background_ingestion'):
            await app.state.background_ingestion.stop()
            logger.info("✅ Background ingestion service stopped")
    except Exception as e:
        logger.error(f"❌ Error stopping background ingestion: {e}")

    logger.info("🛑 IT Newsfeed API shutting down...")


async def _register_default_sources(source_registry: SourceRegistry) -> None:
    """Register default news sources for continuous background ingestion.

    This function sets up the real data sources:
    - RSS feeds from IT news websites (Tom's Hardware, Ars Technica)
    - Reddit subreddit (r/sysadmin) for IT community discussions
    - Mock source as fallback for testing and reliability

    These sources will be automatically fetched in the background at regular intervals
    to provide continuous news updates for IT professionals.

    Potential Pitfalls Addressed:
    - Graceful handling of source registration failures
    - Logging of registered sources for monitoring
    - Integration with existing registry pattern
    """
    try:
        from src.sources.mock_source import MockNewsSource
        from src.sources.rss_source import RSSSource
        rss_sources = [
            RSSSource(
                "tomshardware",
                "https://www.tomshardware.com/feeds/all",
                max_items=10
            ),
            RSSSource(
                "arstechnica",
                "https://feeds.arstechnica.com/arstechnica/index",
                max_items=10
            )
        ]
        for source in rss_sources:
            source_registry.register(source)
            logger.info(f"📰 Registered RSS source: {source.name}")
        mock_source = MockNewsSource("mock_fallback", item_count=5)
        source_registry.register(mock_source)
        logger.info(f"🎭 Registered mock source: {mock_source.name}")

        # Register Reddit source if credentials are available
        try:
            from src.sources.reddit_source import create_reddit_source
            reddit_source = create_reddit_source(subreddit_name="sysadmin", limit=10)
            if reddit_source:
                source_registry.register(reddit_source)
                logger.info(f"📱 Registered Reddit source: {reddit_source.get_source_name()}")
            else:
                logger.info("📱 Reddit source not registered - credentials not available")
        except Exception as e:
            logger.warning(f"📱 Reddit source registration failed: {e}")
            logger.info("Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET to enable Reddit source")
        total_sources = source_registry.count()
        logger.info(
            f"📊 Total sources registered: {total_sources}"
        )
    except Exception as e:
        logger.error(f"❌ Error registering default sources: {e}")
        # Continue startup even if source registration fails
        # This ensures the API remains functional for manual ingestion


async def _register_default_filters(filter_registry: FilterRegistry) -> None:
    """Register default filters for content filtering.

    This function sets up the filtering system:
    - Keyword filter for IT-relevant terms (security, outages, bugs, CVE)
    - Semantic filter for AI-powered content understanding
    - Both filters work together to identify news relevant to IT managers

    These filters will be applied to all ingested items to ensure only
    relevant content is stored and retrieved.

    Potential Pitfalls Addressed:
    - Graceful handling of filter registration failures
    - Logging of registered filters for monitoring
    - Integration with existing filter registry
    """
    try:
        from src.filters.keyword_filter import KeywordFilter
        from src.filters.semantic_filter import SemanticFilter

        # Register keyword filter for IT-relevant terms
        keyword_filter = KeywordFilter()
        filter_registry.register(keyword_filter)
        logger.info(f"🔍 Registered keyword filter: {keyword_filter.name}")

        # Register semantic filter for AI-powered filtering
        semantic_filter = SemanticFilter()
        filter_registry.register(semantic_filter)
        logger.info(f"🤖 Registered semantic filter: {semantic_filter.name}")

        logger.info(f"📊 Total filters registered: {filter_registry.count()}")

    except Exception as e:
        logger.error(f"❌ Error registering default filters: {e}")
        # Continue startup even if filter registration fails
        # This ensures the API remains functional for manual ingestion


# Create FastAPI app with proper configuration
app = FastAPI(
    title="IT Newsfeed API",
    description="Real-time IT newsfeed system with AI-powered semantic filtering",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Global HTTP exception handler with structured logging."""
    logger.error(f"HTTP {exc.status_code}: {exc.detail} for {request.url}")
    if exc.status_code == 400:
        return JSONResponse(
            status_code=400,
            content=BadRequestErrorResponse(
                error="Bad Request",
                status_code=400,
                path=request.url.path,
                details=[
                    {"type": "bad_request", "msg": exc.detail}
                ]
            ).model_dump()
        )
    elif exc.status_code == 500:
        return JSONResponse(
            status_code=500,
            content=InternalServerErrorResponse(
                error="Internal Server Error",
                status_code=500,
                path=request.url.path,
                details=[
                    {"type": "internal_error", "msg": "An unexpected error occurred"}
                ]
            ).model_dump()
        )
    else:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP Error",
                "status_code": exc.status_code,
                "path": request.url.path,
                "details": [
                    {"type": "http_error", "msg": exc.detail}
                ] if exc.detail else None
            }
        )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unexpected errors."""
    logger.error(f"Unexpected error: {exc} for {request.url}")
    return JSONResponse(
        status_code=500,
        content=InternalServerErrorResponse(
            error="Internal Server Error",
            status_code=500,
            path=request.url.path,
            details=[{"type": "internal_error", "msg": "An unexpected error occurred"}]
        ).model_dump()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Custom validation error handler with structured error responses."""
    logger.error(f"Validation error: {exc.errors()} for {request.url}")
    return JSONResponse(
        status_code=422,
        content=ValidationErrorResponse(
            error="Validation Error",
            status_code=422,
            path=request.url.path,
            details=[
                {
                    "type": error["type"],
                    "loc": error["loc"],
                    "msg": error["msg"],
                    "input": error.get("input", "")
                }
                for error in exc.errors()
            ]
        ).model_dump()
    )


@app.get("/", response_model=RootResponse, tags=["Root"], responses={
    200: {"description": "API information retrieved successfully"},
    500: {"model": InternalServerErrorResponse, "description": "Internal server error"}
})
async def read_root() -> RootResponse:
    """Root endpoint with comprehensive API information.

    Provides essential information about the IT Newsfeed API including:
    - API name and purpose
    - Current version
    - Links to documentation and health checks
    - Available endpoints directory

    This is the entry point for API discovery and should be the first endpoint
    called by clients to understand the API structure and capabilities.
    """
    # Build endpoints dynamically based on what's actually available
    endpoints = {
        "ingest": "/api/v1/ingest",
        "retrieve": "/api/v1/retrieve",
        "health": "/health"
    }



    return RootResponse(
        message="IT Newsfeed API",
        description="Real-time IT newsfeed system with AI-powered semantic filtering",
        version="0.1.0",
        docs="/docs",
        health="/health",
        endpoints=endpoints
    )


@app.get("/health", response_model=HealthResponse, tags=["Health"], responses={
    200: {"description": "Health status retrieved successfully"},
    500: {"model": InternalServerErrorResponse, "description": "Internal server error"}
})
async def health_check() -> HealthResponse:
    """Comprehensive health check endpoint with detailed dependency status and explanations.

    Monitors the health of all system components and provides actionable insights:
    - Storage system status (in-memory database)
    - Filter registry status (AI/ML filtering components)
    - Source registry status (data source components)

    Returns detailed explanations for any warnings or errors, including:
    - Specific reasons for degraded status
    - List of registered components
    - Clear guidance on how to resolve issues

    This endpoint is essential for monitoring system health in production
    and helps developers understand the current system state.
    """
    try:
        # Check storage health
        storage_health = {"status": "healthy", "registered": []}
        try:
            await app.state.storage.get_all()
        except Exception as e:
            logger.error(
                f"Storage health check failed: {e}"
            )
            storage_health = {
                "status": "unhealthy",
                "reason": str(e),
                "registered": []
            }

        # Check filter registry health
        filters = []
        filter_health = {"status": "healthy", "registered": []}
        try:
            filters = app.state.filter_registry.list_filters()
            filter_health["registered"] = filters
            if not filters:
                filter_health["status"] = "warning"
                filter_health["reason"] = (
                    "No real filters registered. Register at least one filter "
                    "for full health."
                )
        except Exception as e:
            logger.error(
                f"Filter registry health check failed: {e}"
            )
            filter_health = {
                "status": "unhealthy",
                "reason": str(e),
                "registered": []
            }

        # Check source registry health
        sources = []
        source_health = {"status": "healthy", "registered": []}
        try:
            sources = app.state.source_registry.list_sources()
            source_health["registered"] = sources
            if not sources:
                source_health["status"] = "warning"
                source_health["reason"] = (
                    "No real sources registered. Register at least one source "
                    "for full health."
                )
        except Exception as e:
            logger.error(
                f"Source registry health check failed: {e}"
            )
            source_health = {
                "status": "unhealthy",
                "reason": str(e),
                "registered": []
            }

        overall_status = (
            "healthy"
            if all(
                dep["status"] == "healthy"
                for dep in [storage_health, filter_health, source_health]
            )
            else "degraded"
        )
        return HealthResponse(
            status=overall_status,
            dependencies={
                "storage": DependencyHealth(**storage_health),
                "filters": DependencyHealth(**filter_health),
                "sources": DependencyHealth(**source_health),
            },
            status_explanations={
                "healthy": "All components are fully operational",
                "degraded": (
                    "Some components have warnings but the system is functional"
                ),
                "unhealthy": "Critical components are not working"
            }
        )

    except Exception as e:
        logger.error(
            f"Health check failed: {e}"
        )
        return HealthResponse(
            status="unhealthy",
            dependencies={
                "storage": DependencyHealth(status="unknown", reason=str(e)),
                "filters": DependencyHealth(status="unknown", reason=str(e)),
                "sources": DependencyHealth(status="unknown", reason=str(e)),
            },
        )


# Include routers
app.include_router(ingest.router, prefix="/api/v1", tags=["Ingest"])
app.include_router(retrieve.router, prefix="/api/v1", tags=["Retrieve"])
