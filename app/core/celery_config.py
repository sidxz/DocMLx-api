import os
from celery import Celery
from dotenv import load_dotenv
from app.core.logging_config import logger
from app.hooks.registry import load_hooks_from_directory
# Load environment variables from a .env file if present
load_dotenv()

broker = os.getenv("REDIS_BROKER_URL", "redis://localhost:6379/0")
backend = os.getenv("REDIS_BACKEND_URL", "redis://localhost:6379/0")


celery_app = Celery(
    "tasks",
    broker=broker,
    backend=backend,
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
)


celery_app.autodiscover_tasks(['app.pipeline.presentation_summarization'])


hooks_directory = os.path.join(os.path.dirname(__file__), "..", "hooks")
logger.info("Loading hooks for Celery workers....")
load_hooks_from_directory(hooks_directory)