import importlib.util
import os
from typing import Dict, List, Callable
from app.core.logging_config import logger

# Dictionary to maintain pipeline-specific hooks
pipeline_hooks: Dict[str, List[Callable]] = {}


def register_hook(pipeline: str, hook: Callable):
    """
    Register a callable hook for a specific pipeline.
    """
    if not callable(hook):
        raise ValueError("Hook must be callable.")
    if pipeline not in pipeline_hooks:
        pipeline_hooks[pipeline] = []
    pipeline_hooks[pipeline].append(hook)
    logger.info(f"Hook registered for pipeline '{pipeline}': {hook.__name__}")


def execute_hooks(pipeline: str, document):
    """
    Execute all hooks for the specified pipeline with the provided data.
    """
    hooks = pipeline_hooks.get(pipeline, [])
    for hook in hooks:
        try:
            logger.info(f"Executing hook for pipeline '{pipeline}': {hook.__name__}")
            hook(document=document)
        except Exception as e:
            logger.error(
                f"Error executing hook '{hook.__name__}' in pipeline '{pipeline}': {e}"
            )


def load_hooks_from_directory(base_path: str):
    """
    Dynamically load and register hooks from the directory.
    Folders are treated as pipelines.
    """
    for pipeline_folder in os.listdir(base_path):
        pipeline_path = os.path.join(base_path, pipeline_folder)
        if os.path.isdir(pipeline_path):
            logger.info(f"Loading hooks for pipeline: {pipeline_folder}")
            for file in os.listdir(pipeline_path):
                if file.endswith(".py") and file != "__init__.py":
                    module_name = f"app.hooks.{pipeline_folder}.{file[:-3]}"
                    try:
                        module = importlib.import_module(module_name)
                        if hasattr(module, "hooks") and isinstance(module.hooks, list):
                            for hook in module.hooks:
                                register_hook(pipeline_folder, hook)
                    except Exception as e:
                        logger.error(f"Failed to load hook from {module_name}: {e}")
