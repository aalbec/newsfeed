"""Core news item model with exact API contract compliance."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class NewsItem(BaseModel):
    """News item model matching the exact API contract specification.

    Required fields by API contract:
    - id: string, unique identifier
    - source: string, source name
    - title: string, news title
    - published_at: ISO-8601/RFC 3339 timestamp, UTC

    Optional fields by API contract:
    - body: string, news content (optional)

    Additional fields for internal use:
    - version: int, event versioning for updates/corrections (not part of API contract)
    """

    model_config = ConfigDict(
        # Example data for OpenAPI documentation
        json_schema_extra={
            "example": {
                "id": "news_001",
                "source": "reddit",
                "title": "Critical Security Vulnerability in Apache Log4j",
                "body": (
                    "A zero-day vulnerability has been discovered in "
                    "Apache Log4j..."
                ),
                "published_at": "2024-12-10T15:30:00Z",
                "version": 1
            }
        }
    )

    id: str = Field(..., description="Unique identifier for the news item")
    source: str = Field(..., description="Source name (e.g., 'reddit', 'rss')")
    title: str = Field(..., description="News title")
    body: Optional[str] = Field(
        None, description="News content (optional)"
    )
    published_at: datetime = Field(
        ..., description="Publication timestamp UTC"
    )
    version: int = Field(
        default=1, description="Event version for updates/corrections"
    )

    @field_serializer('published_at')
    def serialize_published_at(self, value: datetime) -> str:
        """Serialize datetime to ISO-8601 format with 'Z' suffix for UTC.

        Required by assignment: published_at (ISO-8601/RFC 3339 timestamp, UTC)
        Converts Python datetime to ISO-8601 format with 'Z' suffix for UTC.
        """
        return value.isoformat() + 'Z' if value.tzinfo else value.isoformat()

    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate that ID is not empty.

        Required by assignment: id (string, unique)
        Prevents empty or whitespace-only IDs that could cause data corruption.
        """
        if not v or not v.strip():
            raise ValueError('ID cannot be empty')
        return v.strip()

    @field_validator('source')
    @classmethod
    def validate_source(cls, v: str) -> str:
        """Validate that source is not empty.

        Required by assignment: source (string)
        Ensures we always know where the news item came from.
        """
        if not v or not v.strip():
            raise ValueError('Source cannot be empty')
        return v.strip()

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate that title is not empty.

        Required by assignment: title (string)
        Prevents news items without meaningful titles.
        """
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()

    @field_validator('body')
    @classmethod
    def validate_body(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize body content.

        Optional by assignment: body (string, optional)
        Converts empty strings to None for consistency.
        Strips whitespace from non-empty content.
        """
        if v is not None and not v.strip():
            return None  # Convert empty string to None
        return v.strip() if v else None

    @field_validator('published_at')
    @classmethod
    def validate_published_at(cls, v: datetime) -> datetime:
        """Ensure datetime is timezone-aware.

        Required by assignment: published_at (ISO-8601/RFC 3339 timestamp, UTC)
        Prevents timezone confusion and ensures consistent datetime handling.
        """
        if v.tzinfo is None:
            raise ValueError('published_at must be timezone-aware')
        return v
