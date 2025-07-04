"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 FastAPI app started!")
    logger.info("🔍 API docs available at http://localhost:8000/docs")
    yield
    logger.info("🛑 FastAPI app shutting down...")


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"message": "Hello, Docker! This is a FastAPI application."}
