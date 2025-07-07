# IT Newsfeed System

A production-ready newsfeed system for aggregating and filtering IT-related news content from multiple sources with modern Python practices and containerized deployment.

**All core functionality is operational and tested:**
- API endpoints (`/ingest`, `/retrieve`, `/health`) are live
- Background ingestion is running and fetching RSS feeds
- AI-powered semantic filtering is working

---

**🚀 Optimized for Fast Testing**

> **NOTE:** The testing suite is optimized for speed. Integration tests run in a dedicated "test mode" that bypasses slow, network-dependent services like AI model loading and background data ingestion. This ensures that even complex integration tests complete quickly and reliably, allowing for efficient development and CI/CD cycles.

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

## Quick Start

### Option 1: Local Development (Recommended for Testing)

```bash
# Clone and setup
git clone https://github.com/aalbec/newsfeed.git
cd newsfeed

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Run the application
python -m src.api.main
```

### Option 2: Docker Development

```bash
# Build and start
make build
make up

# View logs
make logs

# Stop and remove containers
make down
```

### Option 3: Hybrid Docker + Local UI (for Active UI Development)

This approach is useful if you are actively developing the Streamlit dashboard and want to see changes reflected instantly without rebuilding the Docker container.

1.  **Start the Backend**: Run the core API and background services using Docker.
    ```bash
    make up
    ```
2.  **Run the UI Locally**: In a separate terminal, start the Streamlit dashboard. It will automatically connect to the API running in Docker.
    ```bash
    streamlit run src/ui/dashboard.py --server.port 8501
    ```

### Configuration

The system's behavior can be configured using environment variables.

-   `RELEVANCE_THRESHOLD`: Sets the minimum score (from 0.0 to 1.0) for an item to be considered relevant by the API. Defaults to `0.1`.
    ```bash
    export RELEVANCE_THRESHOLD=0.2
    ```

### Reddit API Credentials (Optional)

To enable news aggregation from Reddit, you must provide API credentials. The system will function without them, but the Reddit data source will be disabled.

1.  **Log In and Navigate to App Preferences**:
    First, ensure you are logged into your Reddit account. Then, go directly to the apps preferences page: [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)

2.  **Create a New Application**:
    Scroll to the bottom of the page and click the **"are you a developer? create an app..."** button.

3.  **Fill Out the Application Form**:
    - **Name**: Use the name `IT-Newsfeed-Bot`.
    - **Type**: Select the **`script`** radio button. This is crucial for our use case.
    - **Description**: You can add a brief description, e.g., "Pulls posts from IT subreddits."
    - **About URL**: Use `http://localhost`.
    - **Redirect URI**: Use `http://localhost:8080`.

4.  **Create the App and Get Credentials**:
    Click the **"create app"** button. After the app is created, you will see:
    - The **Client ID** is the string of characters located under the application name.
    - The **Client Secret** is the long string of characters next to the `secret` label.

5.  **Create a `.env` file** in the root of the project directory.

6.  **Add your credentials** to the file in the following format:

    ```ini
    # Reddit API Credentials
    # Get these from https://www.reddit.com/prefs/apps
    # Create a new app with type "Script"
    REDDIT_CLIENT_ID="your_client_id"
    REDDIT_CLIENT_SECRET="your_client_secret"
    REDDIT_USER_AGENT=IT-Newsfeed-Bot/1.0

    # Optional: Customize Reddit subreddit and limit
    REDDIT_SUBREDDIT=sysadmin
    REDDIT_LIMIT=10

    # Other environment variables
    PYTHONUNBUFFERED=1
    RELEVANCE_THRESHOLD=0.1
    ```

The application will automatically load these variables when it starts.

### Access the Application

- **API**: [http://localhost:8000](http://localhost:8000)
- **Interactive Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
- **Dashboard**: [http://localhost:8501](http://localhost:8501) (after starting UI)

### Start the Dashboard

```bash
# Start the dashboard directly
streamlit run src/ui/dashboard.py --server.port 8501
```

## Startup Sequence & Troubleshooting

To avoid dashboard connection errors and ensure a smooth startup, follow this sequence every time:

### 1. Open Two Terminal Windows
You'll need one terminal for the API and one for the dashboard.

### 2. Terminal 1: Start the API

Activate your virtual environment (if not already active):
```bash
source venv/bin/activate
```
Start the API using Uvicorn:
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```
Wait until you see log messages like "API docs available at http://localhost:8000/docs" and no errors.

(Optional) Test the API health endpoint in a new terminal or browser:
```bash
curl http://localhost:8000/health
```
You should see a JSON response with `"status": "healthy"`.

### 3. Terminal 2: Start the Dashboard

Activate your virtual environment (if not already active):
```bash
source venv/bin/activate
```
Start the dashboard:
```bash
streamlit run src/ui/dashboard.py --server.port 8501
```
Wait for the message:
  You can now view your Streamlit app in your browser. Local URL: http://localhost:8501

### 4. Open the Dashboard in Your Browser
Go to [http://localhost:8501](http://localhost:8501).

### 5. If You See "No News Items Available"
Ingest test data using the API (from any terminal):
```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "id": "test_001",
        "source": "test",
        "title": "Critical Security Vulnerability in Apache Log4j",
        "body": "A zero-day vulnerability has been discovered in Apache Log4j that allows remote code execution.",
        "published_at": "2024-12-10T15:30:00Z",
        "version": 1
      }
    ]
  }'
```
Refresh the dashboard page.

### Why This Works
- The dashboard only works if the API is already running and healthy.
- If you start the dashboard before the API is ready, you may get a connection timeout.
- Ingesting test data ensures there's something to display.

### Summary Table
| Step                | What to Do                                 | Why?                        |
|---------------------|--------------------------------------------|-----------------------------|
| 1. Start API        | `uvicorn ...`                              | API must be running first   |
| 2. Check API health | `curl http://localhost:8000/health`        | Ensure API is ready         |
| 3. Start dashboard  | `streamlit run ...`                        | Dashboard connects to API   |
| 4. Ingest data      | `curl -X POST ...`                         | Populate newsfeed           |
| 5. Refresh dashboard| Open/refresh http://localhost:8501         | See news items              |

If you see a timeout or connection error, wait a few seconds and refresh the dashboard after confirming the API is healthy.

---

## Live Testing Examples

### Test the API Endpoints

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
        "published_at": "2024-12-10T15:30:00Z",
        "version": 1
      }
    ]
  }'

# 4. Retrieve again to see new data
curl http://localhost:8000/api/v1/retrieve
```

### Expected Results

- **Health Check**: Returns system status with all dependencies healthy
- **Retrieve**: Returns filtered news items with relevance scores and breakdowns
- **Ingest**: Returns ACK with processing summary (accepted/rejected counts)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | System health and dependency status |
| `/api/v1/ingest` | POST | Ingest raw news events |
| `/api/v1/retrieve` | GET | Retrieve filtered news events |
| `/docs` | GET | Interactive API documentation |

### API Contract Compliance

**Ingest Endpoint (`/api/v1/ingest`):**
- Accepts JSON array of event objects
- Required fields: `id`, `source`, `title`, `published_at`
- Optional fields: `body`, `version`
- Returns HTTP 200 with ACK and processing summary

**Retrieve Endpoint (`/api/v1/retrieve`):**
- Returns filtered events in same JSON format
- Sorted by relevance score × recency
- Deterministic for given ingestion batch
- Includes relevance scores and breakdowns

## Project Structure

```bash
newsfeed/
├── src/                  # Source code (models-first architecture)
│   ├── api/              # FastAPI endpoints and routers
│   │   ├── main.py       # FastAPI application entry point
│   │   └── routers/      # API route handlers
│   │       ├── ingest.py # /api/v1/ingest endpoint
│   │       └── retrieve.py # /api/v1/retrieve endpoint
│   ├── models/           # Core data models (NewsItem, etc.)
│   ├── storage/          # NewsStore abstraction + implementations
│   ├── registry/         # Source/filter registry pattern
│   ├── filtering/        # Content filtering orchestration
│   ├── filters/          # Individual filter implementations
│   │   ├── keyword_filter.py # Keyword-based relevance
│   │   └── semantic_filter.py # AI-powered semantic filtering
│   ├── sources/          # Data source implementations
│   ├── ingestion/        # Background ingestion service
│   │   └── background_ingestion.py # Continuous RSS monitoring
│   └── ui/               # Streamlit dashboard UI
├── tests/                # Comprehensive test suite
│   ├── unit/             # Unit tests for components
│   ├── integration/      # Integration tests with FastAPI TestClient
│   └── conftest.py       # Shared fixtures and configuration
├── pyproject.toml        # Modern Python project configuration
├── Dockerfile            # Optimized containerization
├── docker-compose.yml    # Multi-service orchestration
├── Makefile              # Development workflow commands
├── .gitignore            # Git ignore rules
├── .dockerignore         # Docker build optimization
├── .flake8               # Code linting configuration
└── README.md             # This file
```

## Technology Stack

### Backend

- **Python 3.12** - Modern Python with latest features
- **FastAPI** - High-performance async web framework
- **Pydantic v2** - Data validation and serialization
- **Uvicorn** - ASGI server for production deployment

### AI/ML

- **sentence-transformers** - Text embeddings for semantic filtering
- **all-MiniLM-L6-v2** - Pre-trained model for IT topic similarity
- **Hybrid Scoring** - Semantic + keyword + recency ranking

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

## Testing

### Testing Suite (65/65 Tests Passing, 62% Coverage)

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test categories
pytest tests/integration/  # API and workflow tests
pytest tests/unit/         # Component unit tests
```

### Test Categories

- **Integration Tests**: API endpoints, workflow validation
- **Unit Tests**: Models, storage, filtering components
- **Mock Data Tests**: Simulating external APIs (RSS, Reddit)
- **AI Filtering Tests**: Semantic similarity validation

### External Testing

The system is ready for external evaluation:

- **API Contract**: Exact compliance with assignment requirements
- **Deterministic Results**: Same input = same output
- **Live Endpoints**: All endpoints operational and tested
- **OpenAPI Docs**: Complete documentation at `/docs`


The system is production-ready for MVP and demonstrates modern AI/ML practices while maintaining simplicity and reliability.
