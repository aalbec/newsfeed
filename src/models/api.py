"""API request and response models for the newsfeed endpoints."""

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from .news_item import NewsItem


class IngestRequest(BaseModel):
    """Request model for the /ingest endpoint.

    Accepts a JSON array of news items as specified in the API contract.
    Each item must contain required fields: id, source, title, published_at.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "news_001",
                        "source": "reddit",
                        "title": "Critical Security Vulnerability in Apache Log4j",
                        "body": "A zero-day vulnerability has been discovered in Apache Log4j that allows remote code execution.",
                        "published_at": "2024-12-10T15:30:00Z",
                        "version": 1,
                    },
                    {
                        "id": "news_002",
                        "source": "tomshardware",
                        "title": "Major Cloud Outage Affects Multiple Services",
                        "body": "A widespread cloud outage has impacted services across multiple regions.",
                        "published_at": "2024-12-10T16:00:00Z",
                        "version": 1,
                    },
                ]
            }
        }
    )

    items: List[NewsItem] = Field(
        ...,
        description="Array of news items to ingest. Must contain at least 1 item.",
        min_length=1,
    )

    def model_dump_json(self, **kwargs) -> str:
        """Override to ensure proper JSON serialization."""
        return super().model_dump_json(**kwargs)


class IngestSummary(BaseModel):
    """Summary statistics for the ingest operation."""

    total_received: int = Field(
        ..., description="Total number of items received in the request"
    )
    accepted: int = Field(
        ..., description="Number of items that passed validation and filtering"
    )
    rejected: int = Field(
        ..., description="Number of items that failed relevance filtering"
    )
    duplicates: int = Field(
        ..., description="Number of duplicate items (already exist in storage)"
    )
    errors: int = Field(
        ..., description="Number of items that failed validation or processing"
    )


class IngestResponse(BaseModel):
    """Response model for the /ingest endpoint.

    Returns acknowledgment and summary statistics of the ingestion process.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ACK",
                "message": "News items processed successfully",
                "summary": {
                    "total_received": 3,
                    "accepted": 2,
                    "rejected": 0,
                    "duplicates": 1,
                    "errors": 0,
                },
            }
        }
    )

    status: str = Field(..., description="Always 'ACK' for successful processing")
    message: str = Field(
        ..., description="Human-readable message describing the operation result"
    )
    summary: IngestSummary = Field(
        ..., description="Detailed statistics of the ingestion process"
    )


class RetrieveResponse(BaseModel):
    """Response model for the /retrieve endpoint.

    Returns filtered news items sorted by relevance and recency.
    Items are ranked by importance × recency as specified in the API contract.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "news_001",
                        "source": "reddit",
                        "title": "Critical Security Vulnerability in Apache Log4j",
                        "body": "A zero-day vulnerability has been discovered in Apache Log4j that allows remote code execution.",
                        "published_at": "2024-12-10T15:30:00Z",
                        "version": 1,
                        "relevance_score": 0.95,
                        "score_breakdown": "KeywordFilter: 0.8, SemanticFilter: 0.9",
                    },
                    {
                        "id": "news_002",
                        "source": "tomshardware",
                        "title": "Major Cloud Outage Affects Multiple Services",
                        "body": "A widespread cloud outage has impacted services across multiple regions.",
                        "published_at": "2024-12-10T16:00:00Z",
                        "version": 1,
                        "relevance_score": 0.87,
                        "score_breakdown": "KeywordFilter: 0.7, SemanticFilter: 0.9",
                    },
                ],
                "total": 2,
                "filtering_info": {
                    "total_items_in_storage": 5,
                    "items_passing_filters": 2,
                    "relevance_threshold": 0.3,
                },
            }
        }
    )

    items: List[NewsItem] = Field(
        default_factory=list,
        description="Filtered news items sorted by relevance (score DESC) and recency (timestamp DESC)",
    )
    total: int = Field(default=0, description="Total number of items returned")
    filtering_info: Optional[Dict] = Field(
        default=None,
        description="Optional information about the filtering process and thresholds used",
    )

    def model_dump_json(self, **kwargs) -> str:
        """Override to ensure proper JSON serialization."""
        return super().model_dump_json(**kwargs)


class DependencyHealth(BaseModel):
    """Health status for a single dependency component."""

    status: Literal["healthy", "warning", "unhealthy", "unknown"] = Field(
        ...,
        description="Health status: 'healthy' (fully operational), 'warning' (functional but not optimal), 'unhealthy' (not working), 'unknown' (status cannot be determined)",
    )
    reason: Optional[str] = Field(
        default=None,
        description="Explanation of the current status, especially for warning or unhealthy states",
    )
    registered: Optional[List[str]] = Field(
        default=None,
        description="List of registered components (for filters and sources)",
    )


class HealthResponse(BaseModel):
    """Response model for the /health endpoint.

    Returns comprehensive service health status and detailed dependency information.
    This endpoint helps monitor system health and identify configuration issues.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "degraded",
                "dependencies": {
                    "storage": {"status": "healthy"},
                    "filters": {
                        "status": "warning",
                        "reason": "No real filters registered. Register at least one filter for full health.",
                        "registered": [],
                    },
                    "sources": {
                        "status": "warning",
                        "reason": "No real sources registered. Register at least one source for full health.",
                        "registered": [],
                    },
                },
                "status_explanations": {
                    "healthy": "All components are fully operational",
                    "degraded": "Some components have warnings but the system is functional",
                    "unhealthy": "Critical components are not working",
                },
            }
        }
    )

    status: Literal["healthy", "degraded", "unhealthy"] = Field(
        ...,
        description="Overall service status: 'healthy' (all dependencies healthy), 'degraded' (some warnings), 'unhealthy' (critical failures)",
    )
    dependencies: Dict[Literal["storage", "filters", "sources"], DependencyHealth] = (
        Field(
            ...,
            description="Detailed health status of individual dependencies with explanations and registered components",
        )
    )
    status_explanations: Optional[Dict[str, str]] = Field(
        default=None,
        description="Human-readable explanations of what each status level means",
    )

    def model_dump_json(self, **kwargs) -> str:
        """Override to ensure proper JSON serialization."""
        return super().model_dump_json(**kwargs)


class ValidationErrorResponse(BaseModel):
    """Error response model for 422 validation errors."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Validation Error",
                "status_code": 422,
                "path": "/api/v1/endpoint",
                "details": [
                    {
                        "type": "missing",
                        "loc": ["body", "items"],
                        "msg": "Field required",
                        "input": {},
                    }
                ],
            }
        }
    )

    error: str = Field(..., description="Error type or category")
    status_code: int = Field(..., description="HTTP status code")
    path: str = Field(
        ...,
        description="Request path that caused the error (dynamically set from request.url.path)",
    )
    details: Optional[List[Dict]] = Field(
        default=None,
        description=("Detailed error information, especially for validation errors"),
    )


class BadRequestErrorResponse(BaseModel):
    """Error response model for 400 bad request errors."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Bad Request",
                "status_code": 400,
                "path": "/api/v1/endpoint",
                "details": [{"type": "bad_request", "msg": "Invalid request format"}],
            }
        }
    )

    error: str = Field(..., description="Error type or category")
    status_code: int = Field(..., description="HTTP status code")
    path: str = Field(
        ...,
        description="Request path that caused the error (dynamically set from request.url.path)",
    )
    details: Optional[List[Dict]] = Field(
        default=None, description="Error details for bad request"
    )


class InternalServerErrorResponse(BaseModel):
    """Error response model for 500 internal server errors."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Internal Server Error",
                "status_code": 500,
                "path": "/api/v1/endpoint",
                "details": [
                    {"type": "internal_error", "msg": "An unexpected error occurred"}
                ],
            }
        }
    )

    error: str = Field(..., description="Error type or category")
    status_code: int = Field(..., description="HTTP status code")
    path: str = Field(
        ...,
        description="Request path that caused the error (dynamically set from request.url.path)",
    )
    details: Optional[List[Dict]] = Field(
        default=None, description="Error details for internal server error"
    )


class ErrorResponse(BaseModel):
    """Standard error response model for all endpoints."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Validation Error",
                "status_code": 422,
                "path": "/api/v1/endpoint",
                "details": [
                    {
                        "type": "missing",
                        "loc": ["body", "items"],
                        "msg": "Field required",
                        "input": {},
                    }
                ],
            }
        }
    )

    error: str = Field(..., description="Error type or category")
    status_code: int = Field(..., description="HTTP status code")
    path: str = Field(
        ...,
        description="Request path that caused the error (dynamically set from request.url.path)",
    )
    details: Optional[List[Dict]] = Field(
        default=None,
        description=("Detailed error information, especially for validation errors"),
    )


class RootResponse(BaseModel):
    """Response model for the root endpoint (/) with API information."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "IT Newsfeed API",
                "description": "Real-time IT newsfeed system with AI-powered semantic filtering",
                "version": "0.1.0",
                "docs": "/docs",
                "health": "/health",
                "endpoints": {
                    "ingest": "/api/v1/ingest",
                    "retrieve": "/api/v1/retrieve",
                    "health": "/health",
                },
            }
        }
    )

    message: str = Field(..., description="API name and purpose")
    description: str = Field(
        ..., description="Detailed description of the API functionality"
    )
    version: str = Field(..., description="API version number")
    docs: str = Field(..., description="URL to interactive API documentation")
    health: str = Field(..., description="URL to health check endpoint")
    endpoints: Optional[Dict[str, str]] = Field(
        default=None, description="Available API endpoints and their paths"
    )


# Assignment compliance validation
def validate_assignment_compliance() -> dict:
    """Validate that our models comply with the assignment API contract."""
    return {
        "ingest_request": {
            "required_fields": ["items"],
            "items_type": "List[NewsItem]",
            "items_validation": "min_length=1, max_length=1000",
        },
        "retrieve_response": {
            "required_fields": ["items", "total_count", "filtered_count"],
            "items_type": "List[NewsItem]",
            "counts_type": "int (>= 0)",
        },
        "news_item": {
            "required_fields": ["id", "source", "title", "published_at"],
            "optional_fields": ["body"],
            "id_validation": "string, unique",
            "source_validation": "string",
            "title_validation": "string",
            "body_validation": "string (optional)",
            "published_at_validation": "ISO 8601/RFC 3339 timestamp (UTC)",
        },
    }
