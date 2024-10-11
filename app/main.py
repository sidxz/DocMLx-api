from contextlib import asynccontextmanager
from http.client import HTTPException
import json
import os
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import StreamingResponse
import time
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.api.v1 import mlx
from app.core.logging_config import logger

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code executed before the application starts
    logger.info("Application startup")
    logger.info("Creating Uploads directory")
    UPLOAD_DIRECTORY = os.getenv("UPLOAD_DIRECTORY")
    os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
    logger.info("Ready to accept requests")
    yield
    # Shutdown code executed when the application is stopping
    logger.info("Application shutdown")


app = FastAPI(lifespan=lifespan)

# Add CORS Middleware to allow requests from the frontend (React app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(mlx.router, prefix="/mlx", tags=["mlx"])
