from datetime import datetime

import pytz
from app.core.logging_config import logger
from app.utils.daikon_api import add_or_update_document, get_document_by_path


def serialize_datetime(dt):
    """Helper function to convert datetime to ISO format or return None."""
    if not isinstance(dt, datetime):
        return None
    # Ensure the datetime is in UTC
    dt_utc = dt.astimezone(pytz.utc)
    # Format as ISO 8601 with 'Z' to indicate UTC
    return dt_utc.isoformat(timespec='milliseconds').replace("+00:00", "Z")


def post_to_daikon(document):
    """
    Hook to process and post data to Daikon.

    Args:
        document (object): An object containing metadata about the document.
        results (dict): The results data to be processed.

    Returns:
        bool: True if the operation succeeds, False otherwise.
    """
    logger.info("[START HOOK] POST results to Daikon")

    try:
        # Retrieve the document from Daikon using the provided path
        logger.debug(f"Attempting to retrieve document with path: {document.file_path}")
        existing_document = get_document_by_path(document.file_path)
        # existing_document = None

        if not existing_document:
            # Document does not exist; create a new document entry
            logger.info(
                f"Document does not exist in Daikon. Creating new document entry {document.file_path}"
            )
            new_document = {
                "name": document.file_path.split("/")[
                    -1
                ],  # Extract the filename from the path
                "filePath": document.file_path,
                "externalPath": document.ext_path,
                "fileType": document.file_type,
                "docHash": document.doc_hash,
                "authors": ", ".join(document.authors) if document.authors else None,
                "title": document.title,
                "shortSummary": document.short_summary,
                "tags": document.tags,
                "publicationDate": serialize_datetime(
                    document.date_published
                ),  # Ensure datetime is serialized
            }
            add_or_update_document(new_document)
            logger.info("New document successfully created in Daikon.")
        else:
            # Document exists; update it with new information
            logger.info(
                f"Document exists in Daikon. Updating document entry {document.file_path}"
            )
            existing_document["docHash"] = document.doc_hash
            existing_document["fileType"] = document.file_type
            existing_document["externalPath"] = document.ext_path
            existing_document["authors"] = (
                ", ".join(document.authors) if document.authors else None
            )
            existing_document["title"] = document.title
            existing_document["shortSummary"] = document.short_summary
            if "tags" not in existing_document or existing_document["tags"] is None:
                existing_document["tags"] = []
            if document.tags:
                existing_document["tags"] = list(
                    set(existing_document["tags"] + document.tags)
                )
            existing_document["publicationDate"] = serialize_datetime(
                document.date_published
            )  # Ensure datetime is serialized
            add_or_update_document(existing_document)
            logger.info("Existing document successfully updated in Daikon.")

        return True

    except Exception as error:
        # Log and gracefully handle unexpected errors
        logger.error(f"An error occurred during Daikon document processing: {error}")
        return False

    finally:
        logger.info("[END HOOK] POST results to Daikon.")


hooks = [post_to_daikon]
