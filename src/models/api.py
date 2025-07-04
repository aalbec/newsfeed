"""API request and response models for the newsfeed endpoints."""

from typing import List

from pydantic import BaseModel, ConfigDict, Field

from .news_item import NewsItem


class IngestRequest(BaseModel):
    """Request model for the /ingest endpoint.

    Accepts a JSON array of news items as specified in the API contract.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "news_001",
                        "source": "reddit",
                        "title": (
                            "Critical Security Vulnerability in Apache Log4j"
                        ),
                        "body": (
                            "A zero-day vulnerability has been "
                            "discovered..."
                        ),
                        "published_at": "2024-12-10T15:30:00Z",
                        "version": 1
                    }
                ]
            }
        }
    )

    items: List[NewsItem] = Field(
        ...,
        description="Array of news items to ingest",
        min_length=1
    )


class RetrieveResponse(BaseModel):
    """Response model for the /retrieve endpoint.

    Returns filtered news items sorted by relevance and recency.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "news_001",
                        "source": "reddit",
                        "title": (
                            "Critical Security Vulnerability in Apache Log4j"
                        ),
                        "body": (
                            "A zero-day vulnerability has been "
                            "discovered..."
                        ),
                        "published_at": "2024-12-10T15:30:00Z",
                        "version": 1
                    }
                ],
                "total": 1
            }
        }
    )

    items: List[NewsItem] = Field(
        default_factory=list,
        description="Filtered news items sorted by relevance and recency"
    )
    total: int = Field(
        default=0,
        description="Total number of items returned"
    )
