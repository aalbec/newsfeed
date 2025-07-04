# Newsfeed Project

A production-ready newsfeed system for aggregating and filtering IT-related news content from multiple sources with modern Python practices and containerized deployment.

## Project Overview

This system aggregates IT-related news from RSS feeds, Reddit, and mock APIs, filters content for relevance to IT managers (outages, security, bugs, CVE), and provides both REST API endpoints and a user interface for accessing filtered news items.

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

```bash
newsfeed/
├── src/                  # Source code (models-first architecture)
│   ├── api/              # FastAPI endpoints and routers
│   │   └── main.py       # FastAPI application entry point
│   ├── models/           # Core data models (NewsItem, etc.)
│   ├── storage/          # NewsStore abstraction + implementations
│   ├── registry/         # Source/filter registry pattern
│   ├── filtering/        # Content filtering logic
│   ├── sources/          # Data source implementations
│   └── ui/               # Streamlit dashboard + templates
├── tests/                # Comprehensive test suite
│   ├── unit/             # Unit tests for components
│   ├── integration/      # Integration tests with FastAPI TestClient
│   └── conftest.py       # Shared fixtures and configuration
├── materials/            # Assignment documentation (gitignored)
├── pyproject.toml        # Modern Python project configuration
├── Dockerfile            # Optimized containerization
├── docker-compose.yml    # Multi-service orchestration
├── Makefile              # Development workflow commands
├── .gitignore            # Git ignore rules
├── .dockerignore         # Docker build optimization
└── README.md             # This file
```

## Getting Started

### Prerequisites

- Python 3.12+
- Docker and Docker Compose
- Git

### Local Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd newsfeed

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Run the application
uvicorn src.api.main:app --reload
```

### Docker Development Setup

```bash
# Build and start the application
make build
make up

# View logs
make logs

# Stop the application
make down

# Access shell in container
make shell
```

### Access the Application

- **API**: [http://localhost:8000](http://localhost:8000)
- **Interactive Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative Docs**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Technology Stack

### Backend

- **Python 3.12** - Modern Python with latest features
- **FastAPI** - High-performance async web framework
- **Pydantic v2** - Data validation and serialization
- **Uvicorn** - ASGI server for production deployment

### AI/ML

- **sentence-transformers** - Text embeddings for content filtering
- **Hugging Face transformers** - Advanced NLP models (Phase 1)

### Data Sources

- **feedparser** - RSS feed parsing (Tom's Hardware, Ars Technica)
- **praw** - Reddit API integration (r/sysadmin)
- **httpx** - Modern HTTP client for external APIs

### User Interface

- **Streamlit** - Interactive dashboard
- **FastAPI templates** - Web-based interface

### Observability & Testing

- **Loguru** - Structured logging with JSON output
- **pytest** - Comprehensive testing framework
- **FastAPI TestClient** - API testing utilities

### Containerization & DevOps

- **Docker** - Application containerization
- **Docker Compose** - Multi-service orchestration
- **Make** - Development workflow automation

## Development

*(Development setup and running instructions will be added)*

## Testing

### Test Structure

```bash
tests/
├── unit/             # Unit tests for individual components
├── integration/      # Integration tests with FastAPI TestClient
└── conftest.py       # Shared fixtures and configuration
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test categories
pytest tests/unit/
pytest tests/integration/

# Run tests with verbose output
pytest -v
```

### Test Coverage

- **Unit Tests**: Individual component testing (models, storage, filtering)
- **Integration Tests**: API endpoint testing with FastAPI TestClient
- **Mock Data**: Reliable testing with controlled data sources
- **Fixtures**: Shared test data and FastAPI client setup

### External Testing

The system supports external testing via the provided API endpoints:

- **`/ingest`** - Test data ingestion with JSON payloads
- **`/retrieve`** - Test filtered data retrieval
- **OpenAPI docs** - Available at [http://localhost:8000/docs](http://localhost:8000/docs)

## Reflection Document

A comprehensive reflection document will be included covering:

- Architecture and implementation decisions
- Assumptions and design choices
- Testing and verification methods
- Future improvements and extensions
