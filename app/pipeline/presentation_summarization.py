import os
import uuid
from app.core.celery_config import celery_app
from app.core.logging_config import logger
from typing import Optional

from app.repositories.document_sync import (
    get_document_by_file_path_sync,
    save_document_sync,
)
from app.schema.results.document import Document
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
from app.utils.file_hash import calculate_file_hash
import copy

@celery_app.task(bind=True)
def gen_summary(self, file_location: str, origin_ext_path: str, force_run: bool) -> Optional[Document]:
    """
    Generates a summary for a given document if it is a supported file type (PDF).

    Args:
        file_location (str): The file path to the document.

    Returns:
        Optional[PresentationSummary]: The presentation summary object if the process
        is successful, otherwise None.
    """

    logger.info("[START] Generating document ID and metadata")
    presentation_summary = PresentationSummary()
    document_id = uuid.uuid4()
    run_id = 0
    document = Document(
        id=document_id, file_path=file_location, ext_path=origin_ext_path
    )
    document.file_type = get_file_type(file_location)
    document.doc_hash = calculate_file_hash(file_location)
    logger.info("[END] Generating document ID and metadata")

    # Check if the document already exists in the database and compare hashes
    logger.info("[CHECK] Checking for existing document in the database")
    existing_document = get_document_by_file_path_sync(file_location)

    if existing_document:
        run_id = existing_document.run_id + 1
        document.id = existing_document.id
        document.ext_path = origin_ext_path
        existing_document.ext_path = origin_ext_path
        document.history = copy.deepcopy(existing_document.history)
        if existing_document.doc_hash == document.doc_hash and not force_run:
            logger.info("Document already exists in the database with the same hash.")
            return existing_document.json_serializable()
        else:
            logger.warning(
                "Document exists but hash mismatch. Proceeding with new processing."
            )
    document.run_id = run_id
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
        document.authors = authors
        authors_string = ", ".join(authors)
        document.add_history(run_id ,"Author Extraction", "Success", authors_string)
        logger.info("Author extraction completed successfully.")
    except Exception as e:
        logger.error(f"An error occurred during author extraction: {str(e)}")
        document.add_history(run_id, "Author Extraction", "Failed", str(e))
        return None
    finally:
        logger.info("[END] Extracting author information")

    # Topic Extraction
    try:
        logger.info("[START] Extracting topic information")
        topic = extract_topic_from_first_page(pdf_doc.first_page_content)
        presentation_summary.title = topic
        document.title = topic
        document.add_history(run_id, "Topic Extraction", "Success", topic)
        logger.info("Topic extraction completed successfully.")
    except Exception as e:
        logger.error(f"An error occurred during topic extraction: {str(e)}")
        document.add_history(run_id, "Topic Extraction", "Failed", str(e))
        return None
    finally:
        logger.info("[END] Extracting topic information")

    # Slide Extraction
    try:
        logger.info("[START] Extracting slide information")
        per_slide_summary = create_summary_list(pdf_doc.loaded_docs)
        presentation_summary.per_slide_summary = per_slide_summary
        document.per_slide_summary = per_slide_summary
        document.add_history(run_id, "Slide Extraction", "Success")
        logger.info("Slide extraction completed successfully.")
    except Exception as e:
        logger.error(f"An error occurred during slide extraction: {str(e)}")
        document.add_history(run_id, "Slide Extraction", "Failed", str(e))
        return None
    finally:
        logger.info("[END] Extracting slide information")

    logger.info("Document summary successfully generated.")

    # Short Summary
    try:
        logger.info("[START] Generating short summary")
        short_summary = generate_short_summary(presentation_summary.per_slide_summary)
        presentation_summary.short_summary = short_summary
        document.short_summary = short_summary
        logger.info("Short summary generated successfully.")
        document.add_history(run_id, "Short Summary Generation", "Success", short_summary)
    except Exception as e:
        logger.error(f"An error occurred during short summary generation: {str(e)}")
        document.add_history(run_id, "Short Summary Generation", "Failed", str(e))
        return None
    finally:
        logger.info("[END] Generating short summary")

    # Step 5: Save to MongoDB
    logger.info("[START] Saving results to MongoDB")
    try:
        save_document_sync(document)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    logger.info("[END] Saving results to MongoDB")

    return document.json_serializable()
