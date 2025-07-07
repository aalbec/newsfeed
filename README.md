# IT Newsfeed System

A production-ready newsfeed system for aggregating and filtering IT-related news content from multiple sources with modern Python practices and containerized deployment.

**All core functionality is operational and tested:**
- API endpoints (`/ingest`, `/retrieve`, `/health`) are live
- Background ingestion is running and fetching RSS feeds
- AI-powered semantic filtering is working

---

## Project Overview

This system aggregates IT-related news from RSS feeds, Reddit, and mock APIs, filters content for relevance to IT managers (outages, security, bugs, CVE), and provides both REST API endpoints and a user interface for accessing filtered news items.

## Features

- **Data Aggregation**: Fetches news from RSS feeds (Tom's Hardware, Ars Technica) and mock APIs
- **AI-Powered Content Filtering**: Semantic similarity + keyword matching for IT relevance
- **REST API**: `/ingest` and `/retrieve` endpoints with exact contract compliance
- **Background Ingestion**: Continuous RSS feed monitoring
- **Modular Design**: Registry pattern for easy source/filter extension
- **Comprehensive Testing**: 65/65 tests passing with 62% coverage

## Technology Stack

### Backend
- **Python 3.12** - Modern Python with latest features
- **FastAPI** - High-performance async web framework
- **Pydantic v2** - Data validation and serialization
- **Uvicorn** - ASGI server for production deployment

### AI/ML
- **sentence-transformers** - Text embeddings for semantic filtering
- **all-MiniLM-L6-v2** - Pre-trained model for IT topic similarity
- **Highest-Signal Scoring** - Final score is the MAX of all filter scores
- **Recency-Based Sorting** - Results are sorted by relevance, then by date

### Data Sources
- **feedparser** - RSS feed parsing (Tom's Hardware, Ars Technica)
- **Mock API** - Reliable fallback for testing
- **Background Ingestion** - Continuous RSS monitoring

### Storage & Architecture
- **In-Memory Storage** - Fast MVP implementation
- **Registry Pattern** - Modular sources and filters
- **Storage Abstraction** - Ready for Qdrant migration

### Observability & Testing
- **Loguru** - Structured JSON logging
- **pytest** - Comprehensive testing framework (65/65 tests passing, 62% coverage)
- **Mock Data Testing** - Simulating RSS feeds and external APIs

---

## Quick Start & Configuration

### Step 1: Clone and Install

```bash
# Clone the repository
git clone https://github.com/aalbec/newsfeed.git
cd newsfeed

# Create and activate a virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies in editable mode
pip install -e .
```

### Step 2: Configure Environment Variables (Optional but Recommended)

Create a `.env` file in the project root by copying the example:

```ini
# .env file
# Reddit API Credentials (Optional)
# Get these from https://www.reddit.com/prefs/apps by creating a new "script" app
# About URL: Use http://localhost.
# Redirect URI: Use http://localhost:8080

REDDIT_CLIENT_ID="your_client_id"
REDDIT_CLIENT_SECRET="your_client_secret"
REDDIT_USER_AGENT="IT-Newsfeed-Bot/1.0"
REDDIT_SUBREDDIT=sysadmin
REDDIT_LIMIT=10

# System Configuration
PYTHONUNBUFFERED=1
RELEVANCE_THRESHOLD=0.1
```

- **`RELEVANCE_THRESHOLD`**: Sets the minimum score (from 0.0 to 1.0) for an item to be considered relevant to IT domain by the API. You can increase to `0.3` in order to have an strong filter. Defaults to `0.1`.
- **Reddit Credentials**: To enable the Reddit source, you must provide your own API credentials. Follow the instructions on the [Reddit apps page](https://www.reddit.com/prefs/apps) to create a "script" application.

### Step 3: Choose Your Startup Method

#### Option A: Local Development (Recommended)
Run the application directly for easy debugging.
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Option B: Docker
For a production-like environment.
```bash
# Build and start all services
make up

# View logs
make logs

# Stop and remove containers
make down
```

#### Option C: Hybrid (Docker Backend + Local UI)
Useful for actively developing the UI without rebuilding containers.
```bash
# 1. Start the backend services
make up

# 2. In a separate terminal, start the UI
streamlit run src/ui/dashboard.py --server.port 8501
```

---

## Usage

### Accessing the Application
- **API**: [http://localhost:8000](http://localhost:8000)
- **Interactive Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
- **Dashboard**: [http://localhost:8501](http://localhost:8501)

### Recommended Startup Sequence
To avoid connection errors, always start the API before the dashboard.

1.  **Open two terminals.**
2.  **Terminal 1 (API)**: Start the API using `uvicorn` or `make up`. Wait for it to be ready.
3.  **Terminal 2 (UI)**: Start the dashboard with `streamlit run src/ui/dashboard.py --server.port 8501`.
4.  **Ingest Data (If Needed)**: If the dashboard is empty, send some test data to the `/ingest` endpoint.

### Live Testing with `curl`

```bash
# 1. Check system health
curl http://localhost:8000/health

# 2. Retrieve current filtered news
curl http://localhost:8000/api/v1/retrieve

# 3. Ingest test data
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "id": "test_001",
        "source": "test",
        "title": "Critical Security Vulnerability in Apache Log4j",
        "body": "A zero-day vulnerability has been discovered in Apache Log4j that allows remote code execution.",
        "published_at": "2024-12-10T15:30:00Z"
      }
    ]
  }'

# 4. Retrieve again to see new data
curl http://localhost:8000/api/v1/retrieve
```

---

## API Endpoints & Contract

| Endpoint         | Method | Description                       |
| ---------------- | ------ | --------------------------------- |
| `/health`        | GET    | System health and dependency status |
| `/api/v1/ingest`   | POST   | Ingest raw news events              |
| `/api/v1/retrieve` | GET    | Retrieve filtered news events       |
| `/docs`          | GET    | Interactive API documentation     |

**Ingest Endpoint (`/api/v1/ingest`):**
- Accepts a JSON array of event objects.
- Required fields: `id`, `source`, `title`, `published_at`.
- Returns HTTP 200 with an ACK and processing summary.

**Retrieve Endpoint (`/api/v1/retrieve`):**
- Returns filtered events, sorted by relevance and recency.
- The call is deterministic for a given ingestion batch.

---

## Testing Strategy

**Optimized for Speed:** The testing suite is designed for fast and reliable execution. Integration tests run in a dedicated "test mode" that bypasses slow, network-dependent services like AI model loading, ensuring efficient CI/CD cycles.

### Running Tests
```bash
# Run all tests (65/65 passing)
pytest

# Run with coverage report
pytest --cov=src
```

### Test Categories
- **Integration Tests**: Validate API endpoints and end-to-end workflows.
- **Unit Tests**: Test individual components like models, storage, and filters.
- **Mock Data Tests**: Simulate external APIs (RSS, Reddit) for deterministic results.
- **AI Filtering Tests**: Validate the logic of the semantic similarity and keyword filters.

---

## Project Structure

```bash
newsfeed/
├── src/                  # Source code (models-first architecture)
│   ├── api/              # FastAPI endpoints and routers
│   ├── models/           # Core data models (NewsItem, etc.)
│   ├── storage/          # NewsStore abstraction + implementations
│   ├── registry/         # Source/filter registry pattern
│   ├── filtering/        # Content filtering orchestration
│   ├── filters/          # Individual filter implementations
│   ├── sources/          # Data source implementations
│   ├── ingestion/        # Background data ingestion service
│   └── ui/               # Streamlit dashboard UI
├── tests/                # Comprehensive test suite
│   ├── unit/             # Unit tests for components
│   └── integration/      # Integration tests with FastAPI TestClient
├── pyproject.toml        # Modern Python project configuration
├── Dockerfile            # Optimized containerization
├── docker-compose.yml    # Multi-service orchestration
├── Makefile              # Development workflow commands
└── README.md             # This file
```
