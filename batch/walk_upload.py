import os
import logging
from urllib.parse import quote, urlencode
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Constants
BU_BASE_DIRECTORY = os.getenv("BU_BASE_DIRECTORY")
BU_UPLOAD_URL = os.getenv("BU_UPLOAD_URL")
BU_EXTERNAL_BASE_URL = os.getenv("BU_EXTERNAL_BASE_URL")
BU_FILE_EXTENSION = os.getenv("BU_FILE_EXTENSION", ".pptx")  # Default fallback


def validate_environment_variables():
    """
    Validate required environment variables are set.
    """
    missing_vars = [
        var
        for var in ["BU_BASE_DIRECTORY", "BU_UPLOAD_URL", "BU_EXTERNAL_BASE_URL"]
        if not globals()[var]
    ]
    if missing_vars:
        logging.error(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
        exit(1)


def generate_origin_ext_path(file_path: str) -> str:
    """
    Generate the SharePoint-compatible URL for a given file path.

    Args:
        file_path (str): Full path to the file.

    Returns:
        str: SharePoint-compatible URL path.
    """
    try:
        # Calculate relative path and replace file extension
        relative_path = os.path.relpath(file_path, BU_BASE_DIRECTORY)
        if BU_FILE_EXTENSION:
            relative_path = relative_path.replace(".pdf", BU_FILE_EXTENSION)

        # Encode the path to make it URL-safe
        encoded_relative_path = quote(relative_path)
        return f"{BU_EXTERNAL_BASE_URL}{encoded_relative_path}"
    except Exception as e:
        logging.error(f"Error generating origin_ext_path for {file_path}: {str(e)}")
        raise


def generate_dir_path(file_path: str) -> str:
    """
    Generate the SharePoint-compatible URL for a given file path.

    Args:
        file_path (str): Full path to the file.

    Returns:
        str: SharePoint-compatible URL path.
    """
    try:
        # Calculate relative path and replace file extension
        relative_path = os.path.relpath(file_path, BU_BASE_DIRECTORY)
        dir_path = os.path.dirname(relative_path)

        # Encode the path to make it URL-safe
        encoded_dir_path = quote(dir_path)
        return encoded_dir_path
    except Exception as e:
        logging.error(f"Error generating encoded_dir_path for {file_path}: {str(e)}")
        raise


def upload_file(file_path: str):
    """Upload a file to the FastAPI endpoint."""
    origin_ext_path = generate_origin_ext_path(file_path)
    origin_dir_path = generate_dir_path(file_path)
    try:
        # Construct the query parameter
        params = {
            "origin_ext_path": origin_ext_path,
            "origin_dir_path": origin_dir_path,
            "force_rerun": False,
        }
        query_string = urlencode(params)
        full_url = f"{BU_UPLOAD_URL}?{query_string}"

        # Open the file and set up multipart form-data
        with open(file_path, "rb") as file_data:
            files = {
                "file": (
                    os.path.basename(file_path),
                    file_data,
                    "application/pdf",  # Explicitly set the content type
                )
            }

            # Log the upload attempt
            logging.info(f"Uploading {file_path} \n {origin_ext_path}")

            # Make the POST request
            response = requests.post(full_url, files=files)
            response.raise_for_status()

            # Log success
            logging.info(f"Upload successful: {response.json()}")

    except requests.RequestException as e:
        logging.error(f"HTTP error while uploading {file_path}: {e}")
        if e.response:
            logging.error(f"Response status code: {e.response.status_code}")
            logging.error(f"Response content: {e.response.text}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")


def find_and_upload_files(directory: str):
    """
    Recursively find all PDF files in a directory and upload them.

    Args:
        directory (str): Base directory to search for PDF files.
    """
    try:
        for root, _, files in os.walk(directory):
            for file_name in files:
                if file_name.lower().endswith(".pdf"):
                    file_path = os.path.join(root, file_name)
                    upload_file(file_path)
                    
    except Exception as e:
        logging.error(f"Error while processing directory {directory}: {str(e)}")
        raise


if __name__ == "__main__":
    # Validate environment variables
    validate_environment_variables()

    # Begin file upload process
    try:
        find_and_upload_files(BU_BASE_DIRECTORY)
    except Exception as e:
        logging.critical(f"Critical failure: {str(e)}")
        exit(1)
