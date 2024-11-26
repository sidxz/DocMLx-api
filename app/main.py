from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.api.v1 import mlx
from app.core.logging_config import logger
from app.hooks.registry import load_hooks_from_directory

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code executed before the application starts
    logger.info("Application startup")
    logger.info("Creating Uploads directory")
    UPLOAD_DIRECTORY = os.getenv("UPLOAD_DIRECTORY")
    os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
    
    # Load hooks
    logger.info("Loading hooks....")
    hooks_directory = os.path.join(os.path.dirname(__file__), "hooks")
    load_hooks_from_directory(hooks_directory)
    
    
    logger.info("Ready to accept requests")
    yield
    # Shutdown code executed when the application is stopping
    logger.info("Application shutdown")


app = FastAPI(lifespan=lifespan)

# Add CORS Middleware to allow requests from the frontend (React app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5301"],  # Frontend's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mlx.router, prefix="/mlx", tags=["mlx"])
