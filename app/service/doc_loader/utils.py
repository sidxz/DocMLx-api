from app.core.logging_config import logger
from typing import Optional
import magic
import os


def get_file_type(file_location: str) -> Optional[str]:
    """
    Determines the file type of a given file using the magic library.

    Args:
        file_location (str): The file path to the document.

    Returns:
        Optional[str]: The detected file type as a string, or None if detection fails.
    """
    # Check if the file exists and is accessible
    if not os.path.exists(file_location):
        logger.error(f"File not found: {file_location}")
        return None

    if not os.access(file_location, os.R_OK):
        logger.error(f"Permission denied: Cannot access file at {file_location}")
        return None

    try:
        file_magic = magic.Magic()
        file_type = file_magic.from_file(file_location)
        logger.info(f"Document type: {file_type}")
        return file_type
    except magic.MagicException as me:
        logger.error(f"An error occurred while detecting the file type: {str(me)}")
        return None
    except Exception as e:
        logger.error(
            f"An unexpected error occurred during file type detection: {str(e)}"
        )
        return None
