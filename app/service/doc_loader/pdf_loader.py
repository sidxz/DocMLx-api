from app.core.logging_config import logger
from langchain_community.document_loaders import PyPDFLoader
from typing import Tuple


def load_pdf_document(pdf_location: str) -> Tuple[str, str, str]:
    """
    Load a PDF document from the specified location, extracting the combined content,
    the content of the first page, and the content of the last page.

    Args:
        pdf_location (str): The file path to the PDF document.

    Returns:
        Tuple[str, str, str]: A tuple containing:
            - The combined content of all pages.
            - The content of the first page.
            - The content of the last page.
    """
    try:
        # Logging the action of loading a PDF document
        logger.debug(f"Loading PDF document from {pdf_location}")

        # Initialize the PDF loader
        loader = PyPDFLoader(pdf_location)

        # Load the document
        loaded_docs = loader.load()

        # Check if any pages were loaded successfully
        if not loaded_docs:
            logger.warning("No pages found in the PDF document.")
            return "", "", ""

        # Extract content from the first, all, and the last page
        first_page_content = loaded_docs[0].page_content
        combined_content = " ".join(doc.page_content for doc in loaded_docs)
        last_page_content = loaded_docs[-1].page_content

        return combined_content, first_page_content, last_page_content

    except FileNotFoundError:
        logger.error(f"File not found: {pdf_location}")
        return "", "", ""
    except PermissionError:
        logger.error(f"Permission denied: Unable to access file at {pdf_location}")
        return "", "", ""

    except Exception as e:
        # Catching any other exception and logging it securely without exposing sensitive information
        logger.error(f"An error occurred while loading the PDF document: {str(e)}")
        return "", "", ""
