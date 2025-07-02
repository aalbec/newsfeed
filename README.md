# Newsfeed Project

A real-time newsfeed system for aggregating and displaying IT-related news content from various sources.

## Project Overview

This system aggregates IT-related news from multiple sources, filters content for relevance to IT managers, and provides both a user interface and API for accessing filtered news items.

## Features

- **Data Aggregation**: Fetches news from Reddit subreddits and IT news websites
- **Content Filtering**: Identifies IT-relevant news (outages, security issues, major bugs)
- **REST API**: `/ingest` and `/retrieve` endpoints for data ingestion and retrieval
- **User Interface**: Simple dashboard to display filtered news
- **Modular Design**: Easy to add or remove news sources

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ingest` | POST | Ingest raw news events |
| `/retrieve` | GET | Retrieve filtered news events |

### API Contract

**Ingest Endpoint:**
- Accepts JSON array of event objects
- Each object must contain: `id`, `source`, `title`, `body` (optional), `published_at`
- Returns HTTP 200 acknowledgment

**Retrieve Endpoint:**
- Returns filtered events in same JSON format
- Sorted by relevance and recency
- Deterministic for given ingestion batch

## Project Structure

```
├── src/                   # Source code
│   ├── api/               # REST API endpoints
│   ├── data_sources/      # News source integrations
│   ├── filtering/         # Content filtering logic
│   ├── models/            # Data models
│   └── ui/                # User interface
├── tests/                 # Test files
├── docs/                  # Documentation
├── README.md              # This file
└── .gitignore             # Git ignore rules
```

## Getting Started

*(Development instructions will be added as the project develops)*

## Technology Stack

*(Tech stack will be finalized based on implementation choices)*

## Development

*(Development setup and running instructions will be added)*

## Testing

The system includes automated tests and supports external testing via the provided API endpoints.

## Reflection Document

A comprehensive reflection document will be included covering:
- Architecture and implementation decisions
- Assumptions and design choices
- Testing and verification methods
- Future improvements and extensions 