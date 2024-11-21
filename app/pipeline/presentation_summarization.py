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
from app.service.lm.ppt.summarizers.exec_summary import generate_exec_summary
from app.service.lm.ppt.summarizers.short_summary import generate_short_summary
from app.service.lm.ppt.summarizers.slide_summary import create_summary_list


def gen_summary(file_location: str) -> Optional[PresentationSummary]:
    """
    Generates a summary for a given document if it is a supported file type (PDF).

    Args:
        file_location (str): The file path to the document.

    Returns:
        Optional[PresentationSummary]: The presentation summary object if the process
        is successful, otherwise None.
    """
    presentation_summary = PresentationSummary()

    try:
        logger.info("[START] Pre-processing document")
        logger.info(f"Document location: {file_location}")

        # Validate file existence
        if not os.path.isfile(file_location):
            logger.error(f"File not found: {file_location}")
            return None

        # Identify the file type
        file_type = get_file_type(file_location)

        if "PDF" not in file_type:
            logger.warning("Unsupported document type. Only PDF files are supported.")
            return None

        logger.info("PDF document detected. Proceeding with PDF processing.")
        pdf_doc = load_pdf_document(file_location)

        if not pdf_doc or not pdf_doc.first_page_content:
            logger.error("Failed to load or extract content from PDF document.")
            return None

    except FileNotFoundError:
        logger.error(f"File not found: {file_location}")
        return None
    except Exception as e:
        logger.error(f"An error occurred during document pre-processing: {str(e)}")
        return None
    finally:
        logger.info("[END] Pre-processing document")

    # Author Extraction
    try:
        logger.info("[START] Extracting author information")
        file_name = os.path.basename(file_location)
        authors = extract_author_from_first_page(
            first_page_content=pdf_doc.first_page_content, file_name=file_name
        )
        presentation_summary.authors = authors
        logger.info("Author extraction completed successfully.")
    except Exception as e:
        logger.error(f"An error occurred during author extraction: {str(e)}")
        return None
    finally:
        logger.info("[END] Extracting author information")

    # Topic Extraction
    try:
        logger.info("[START] Extracting topic information")
        topic = extract_topic_from_first_page(pdf_doc.first_page_content)
        presentation_summary.title = topic
        logger.info("Topic extraction completed successfully.")
    except Exception as e:
        logger.error(f"An error occurred during topic extraction: {str(e)}")
        return None
    finally:
        logger.info("[END] Extracting topic information")

    # Slide Extraction
    try:
        logger.info("[START] Extracting slide information")
        per_slide_summary = create_summary_list(pdf_doc.loaded_docs)
        presentation_summary.per_slide_summary = per_slide_summary
        logger.info("Slide extraction completed successfully.")
    except Exception as e:
        logger.error(f"An error occurred during slide extraction: {str(e)}")
        return None
    finally:
        logger.info("[END] Extracting slide information")

    logger.info("Document summary successfully generated.")

    # Short Summary
    try:
        logger.info("[START] Generating short summary")
        short_summary = generate_short_summary(presentation_summary.per_slide_summary)
        presentation_summary.short_summary = short_summary
        logger.info("Short summary generated successfully.")
    except Exception as e:
        logger.error(f"An error occurred during short summary generation: {str(e)}")
        return None
    finally:
        logger.info("[END] Generating short summary")

    # Executive Summary
    try:
        logger.info("[START] Generating executive summary")
        executive_summary = generate_exec_summary(
            content=presentation_summary.per_slide_summary,
            topic=presentation_summary.title,
        )
        presentation_summary.executive_summary = executive_summary
        logger.info("Executive summary generated successfully.")
    except Exception as e:
        logger.error(f"An error occurred during executive summary generation: {str(e)}")
        return None
    finally:
        logger.info("[END] Generating executive summary")

    return presentation_summary
