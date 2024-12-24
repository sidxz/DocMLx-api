from datetime import datetime
import os
import uuid
from app.core.celery_config import celery_app
from app.core.logging_config import logger
from typing import Optional

from app.hooks.registry import execute_hooks
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
from app.service.lm.ppt.extractors.target_extractor import (
    extract_target_from_first_page,
    extract_target_from_summary,
)
from app.service.lm.ppt.extractors.topic_extractor import extract_topic_from_first_page
from app.service.lm.ppt.summarizers.exec_summary import generate_exec_summary
from app.service.lm.ppt.summarizers.short_summary import (
    filter_bullets_summary,
    generate_short_summary,
    shorten_summary,
)
from app.service.lm.ppt.summarizers.slide_summary import create_summary_list
from app.service.nlp.ppt.date_extractor import extract_date
from app.utils.file_hash import calculate_file_hash
import copy

from app.utils.text_processing import contains_bullet_points, count_words_nltk


@celery_app.task(bind=True)
def gen_summary(
    self, file_location: str, origin_ext_path: str, force_run: bool
) -> Optional[Document]:
    """
    Generates a summary for a given document if it is a supported file type (PDF).

    Args:
        file_location (str): The file path to the document.

    Returns:
        Optional[PresentationSummary]: The presentation summary object if the process
        is successful, otherwise None.
    """
    RUN_AUTHOR_EXTRACTION = True
    RUN_TOPIC_EXTRACTION = True
    RUN_SLIDE_EXTRACTION = True
    RUN_SHORT_SUMMARY = True
    RUN_TARGET_EXTRACTION = True
    RUN_DATE_EXTRACTION = True
    RUN_POST_HOOKS = False
    SHORT_SUMMARY_THRESHOLD = 160

    logger.info("[START] Generating document ID and metadata")
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
        logger.info(f"Document found in the database at {existing_document.file_path}.")
        run_id = (
            existing_document.run_id + 1 if existing_document.run_id is not None else 0
        )
        document.id = existing_document.id
        document.ext_path = origin_ext_path
        existing_document.ext_path = origin_ext_path
        document.history = copy.deepcopy(existing_document.history)
        if existing_document.doc_hash == document.doc_hash and not force_run:
            logger.info("Document already exists in the database with the same hash.")
            # Run post hooks
            logger.info("[START] Looking for POST hooks")
            hook_pipeline_post = os.getenv("HOOKS_POST")
            if hook_pipeline_post is not None:
                logger.info(f"[START] Found {hook_pipeline_post}: Executing Post hooks")
                execute_hooks(pipeline=hook_pipeline_post, document=existing_document)

            return existing_document.json_serializable()
        else:
            logger.warning(
                "Document exists but hash mismatch or force run is enabled. Proceeding with new processing."
            )
            document = copy.deepcopy(existing_document)

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
    if RUN_AUTHOR_EXTRACTION:
        try:
            logger.info("[START] Extracting author information")
            file_name = os.path.basename(file_location)
            authors = extract_author_from_first_page(
                first_page_content=pdf_doc.first_page_content, file_name=file_name
            )
            document.authors = authors
            authors_string = ", ".join(authors)
            document.add_history(run_id, "Author Extraction", "Success", authors_string)
            logger.info("Author extraction completed successfully.")
        except Exception as e:
            logger.error(f"An error occurred during author extraction: {str(e)}")
            document.add_history(run_id, "Author Extraction", "Failed", str(e))
            return None
        finally:
            logger.info("[END] Extracting author information")

    # Topic Extraction
    if RUN_TOPIC_EXTRACTION:
        try:
            logger.info("[START] Extracting topic information")
            topic = extract_topic_from_first_page(pdf_doc.first_page_content)
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
    if RUN_SLIDE_EXTRACTION:
        try:
            logger.info("[START] Extracting slide information")
            per_slide_summary = create_summary_list(pdf_doc.loaded_docs)
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
    if RUN_SHORT_SUMMARY:
        try:
            logger.info("[START] Generating short summary")
            short_summary = generate_short_summary(document.per_slide_summary)

            # Detect bullet points
            bullets_present = contains_bullet_points(short_summary)
            if bullets_present:
                document.add_history(
                    run_id,
                    "Short Summary Generation",
                    "Retry",
                    f"Bullet points detected : {short_summary}",
                )
                logger.info("Bullet points detected in the summary.")
                short_summary = filter_bullets_summary(short_summary)

            no_of_words = count_words_nltk(short_summary)
            logger.info(f"Number of words in the summary: {no_of_words}")

            if no_of_words > SHORT_SUMMARY_THRESHOLD:
                document.add_history(
                    run_id,
                    "Short Summary Generation",
                    "Retry",
                    f"Word count exceeded {no_of_words} : {short_summary}",
                )
                logger.info("Re summarizing the summary.")
                short_summary = shorten_summary(short_summary)
                no_of_words = count_words_nltk(short_summary)
                logger.info(
                    f"Number of words in the resummarized summary: {no_of_words}"
                )

            document.short_summary = short_summary
            if no_of_words > SHORT_SUMMARY_THRESHOLD:
                document.add_history(
                    run_id,
                    "Short Summary Generation",
                    "Warning",
                    f"Word count exceeded {no_of_words} : {short_summary}",
                )
                logger.warning(
                    f"Word count exceeded {SHORT_SUMMARY_THRESHOLD}. Will still use the summary."
                )
            else:
                logger.info("Short summary generated successfully.")
                document.add_history(
                    run_id,
                    "Short Summary Generation",
                    "Success",
                    f"({no_of_words}) {short_summary}",
                )
        except Exception as e:
            logger.error(f"An error occurred during short summary generation: {str(e)}")
            document.add_history(run_id, "Short Summary Generation", "Failed", str(e))
            return None
        finally:
            logger.info("[END] Generating short summary")

    # Target Extraction
    if RUN_TARGET_EXTRACTION:
        try:
            logger.info(
                "[START] Extracting target from file name and first page content"
            )
            target = extract_target_from_first_page(
                first_page_content=pdf_doc.first_page_content, file_name=file_name
            )
            if target == "Unknown":
                logger.warning("Target extraction returned 'Unknown'.")
                document.add_history(
                    run_id,
                    "Target Extraction",
                    "Failed",
                    "Target extraction returned 'Unknown'.",
                )
            else:
                document.target = target
                document.add_history(run_id, "Target Extraction", "Success", target)
        except Exception as e:
            logger.error(
                f"An error occurred during target summary generation: {str(e)}"
            )
            document.add_history(run_id, "Target Summary Generation", "Failed", str(e))
            return None
        finally:
            document.target = target
            logger.info("[END] Target Extraction from file name and first page content")

    # Target Extraction from Summary if Target is Unknown
    if RUN_TARGET_EXTRACTION:
        if document.target == "Unknown":
            try:
                logger.info("[START] Extracting target from summary")
                # join document.per_slide_summary into a single string
                summary_string = " ".join(document.per_slide_summary)
                target = extract_target_from_summary(
                    summary=summary_string, topic=document.title
                )
                if target == "Unknown":
                    logger.warning("Target extraction from summary returned 'Unknown'.")
                    document.add_history(
                        run_id,
                        "Target Extraction from Summary",
                        "Failed",
                        "Target extraction from summary returned 'Unknown'.",
                    )
                else:
                    document.target = target
                    document.add_history(
                        run_id, "Target Extraction from Summary", "Success", target
                    )
            except Exception as e:
                logger.error(
                    f"An error occurred during target extraction from summary: {str(e)}"
                )
                document.add_history(
                    run_id, "Target Extraction from Summary", "Failed", str(e)
                )
                return None
            finally:
                logger.info("[END] Extracting target from summary")
    # Tags
    if RUN_TARGET_EXTRACTION:
        if document.target != "Unknown":
            document.tags.append(document.target)

    # Date Extraction
    if RUN_DATE_EXTRACTION:
        try:
            logger.info("[START] Extracting date information")
            file_name = os.path.basename(document.file_path)
            date_published = extract_date(
                file_name=file_name, first_page_content=pdf_doc.first_page_content
            )
            logger.info(f"Date published: {date_published}")
            logger.info(f"Date type: {type(date_published)}")
            # check if type is datetime
            if date_published is not None and isinstance(date_published, datetime):
                document.date_published = date_published
                document.add_history(
                    run_id, "Date Extraction", "Success", date_published.strftime("%Y-%m-%d")
                )
                logger.info("Date extraction completed successfully.")
            else:
                document.add_history(
                    run_id, "Date Extraction", "Failed", "No date found"
                )
                logger.warning("No date found in the document.")

        except Exception as e:
            logger.error(f"An error occurred during date extraction: {str(e)}")
            document.add_history(run_id, "Date Extraction", "Failed", str(e))
            return None
        finally:
            logger.info("[END] Extracting date information")
    # Step 5: Save to MongoDB
    logger.info("[START] Saving results to MongoDB")
    try:
        save_document_sync(document)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    logger.info("[END] Saving results to MongoDB")

    # Step 6: Run Post hooks
    if RUN_POST_HOOKS:
        logger.info("[START] Looking for POST hooks")
        hook_pipeline_post = os.getenv("HOOKS_POST")
        if hook_pipeline_post is not None:
            logger.info(f"[START] Found {hook_pipeline_post}: Executing Post hooks")
            execute_hooks(pipeline=hook_pipeline_post, document=document)
        logger.info("[END] Post hooks")

    return document.json_serializable()
