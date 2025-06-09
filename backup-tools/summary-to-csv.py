import os
import sys

# Add the parent directory to the system path for module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


import pandas as pd
from app.schema.results.document import Document
from app.core.logging_config import logger
from app.repositories.document_sync import get_all_documents_sync


def export_documents_to_csv(filepath: str = "documents_summary.csv") -> None:
    """
    Export selected fields from all documents to a CSV file.

    Fields:
        - file_path
        - ext_path
        - authors
        - date_published
        - short_summary
        - executive_summary
    """
    try:
        logger.info("Fetching all documents for CSV export")
        documents = get_all_documents_sync()

        logger.info(f"Processing {len(documents)} documents")

        rows = []
        for doc in documents:
            rows.append({
                "file_path": doc.file_path,
                "ext_path": doc.ext_path,
                "authors": ", ".join(doc.authors or []),
                "date_published": doc.date_published.isoformat() if doc.date_published else None,
                "short_summary": doc.short_summary,
                "executive_summary": doc.executive_summary,
            })

        df = pd.DataFrame(rows)
        df.to_csv(filepath, index=False)
        logger.info(f"Exported {len(rows)} documents to CSV: {filepath}")

    except Exception as e:
        logger.error(f"Failed to export documents to CSV: {str(e)}")
        raise


export_documents_to_csv(filepath="exports/document_summaries.csv")