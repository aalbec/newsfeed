# Clean Dockerfile with ML support
FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Install system dependencies for ML libraries
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Upgrade pip and install build tools
RUN pip install --upgrade pip setuptools wheel

# Copy pyproject.toml and src directory for package installation
COPY pyproject.toml ./
COPY src/ ./src/

# Install Python dependencies (this is the expensive step but cached)
RUN pip install --no-cache-dir -e .

# Pre-download sentence-transformers model (cached)
RUN python -c "from sentence_transformers import SentenceTransformer; print('Downloading ML model...'); SentenceTransformer('all-MiniLM-L6-v2'); print('ML model ready!')"

# Copy remaining project files
COPY . .

# Set environment variables
ENV RELEVANCE_THRESHOLD=0.1
ENV PYTHONPATH=/app/src

# Expose FastAPI default port
EXPOSE 8000

# Run the FastAPI app with Uvicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
