import os
from app.core.logging_config import logger
from typing import Optional

from app.schema.results.presentation_summary import PresentationSummary
from app.service.doc_loader.utils import get_file_type
from app.service.doc_loader.pdf_loader import load_pdf_document
from app.service.lm.ppt.extractors.author_extractor import (
    extract_author_from_first_page,
)
from app.service.lm.ppt.extractors.topic_extractor import extract_topic_from_first_page


def gen_summary(file_location: str):
    """
    Pre-process the document based on its type. If the document is a PDF, it processes
    the PDF content; otherwise, logs a warning that the file type is not supported.

    Args:
        file_location (str): The file path to the document.
    """

    presentation_summary = PresentationSummary()
    try:
        logger.info("[START] Pre-processing document")
        logger.info(f"Document location: {file_location}")

        # Identify the file type using the magic library
        file_type = get_file_type(file_location)

        # Check if the file type is a PDF
        if "PDF" in file_type:
            logger.info("PDF document detected. Proceeding with PDF processing.")
            combined_content, first_page_content, last_page_content = load_pdf_document(
                file_location
            )

            # Log relevant details for further processing
            logger.info("PDF processing completed successfully.")

            # logger.info(f"First page content: {first_page_content}")
        else:
            logger.warning("Unsupported document type. Only PDF files are supported.")
            return None
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        return None
    finally:
        logger.info("[END] Pre-processing document")

    # Author Extraction
    try:
        logger.info("[START] Extracting author information")
        file_name = os.path.basename(file_location)
        author = extract_author_from_first_page(
            first_page_content=first_page_content, file_name=file_name
        )
        presentation_summary.author = author
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        return None
    finally:
        logger.info("[END] Extracting author information")

    # Topic Extraction
    try:
        logger.info("[START] Extracting topic information")
        topic = extract_topic_from_first_page(first_page_content=first_page_content)
        presentation_summary.topic = topic
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        return None
    finally:
        logger.info("[END] Extracting topic information")
