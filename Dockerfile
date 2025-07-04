# Use official Python image
FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Install pip and build dependencies
RUN pip install --upgrade pip

# Copy only pyproject.toml first (for better caching)
COPY pyproject.toml ./

# Copy src directory (needed for pip install -e .)
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy remaining project files
COPY . .

# Expose FastAPI default port
EXPOSE 8000

# Run the FastAPI app with Uvicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
