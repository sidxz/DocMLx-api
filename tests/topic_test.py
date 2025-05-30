import os
import sys

# Add the parent directory to the system path for module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from app.service.doc_loader.pdf_loader import load_pdf_document
from app.service.lm.ppt.extractors.topic_extractor import (
    extract_topic_from_first_page,
)
import pandas as pd
from tabulate import tabulate
from app.core.logging_config import logger
from app.service.doc_loader.utils import get_file_type
from app.pipeline.presentation_summarization import gen_summary


def process_all_documents(upload_dir: str):
    """
    Processes all files in the specified directory and generates a summary for each.
    The output is presented in a tabular format using pandas.

    Args:
        upload_dir (str): The directory containing the documents.
    """
    if not os.path.isdir(upload_dir):
        logger.error(
            f"The provided directory '{upload_dir}' does not exist or is not a directory."
        )
        return

    results = []

    # Iterate over all files in the uploads directory
    for filename in os.listdir(upload_dir):
        file_location = os.path.join(upload_dir, filename)

        # Process only files (skip directories and other non-file entries)
        if os.path.isfile(file_location):
            logger.debug(f"Processing file: {filename}")
            try:

                pdf_doc = load_pdf_document(file_location)
                file_name = os.path.basename(file_location)
                topic_info = extract_topic_from_first_page(
                    first_page_content=pdf_doc.first_page_content
                )
                results.append(
                    {
                        "File Name": filename,
                        "Topic": topic_info if topic_info else "N/A",  # ✅ Use directly
                    }
                )
            except Exception as e:
                # Log any error encountered during file processing
                logger.error(f"Error processing file '{filename}': {str(e)}")
        else:
            logger.debug(f"Skipping non-file entry: {filename}")

    # Convert the results to a pandas DataFrame for tabular representation
    df = pd.DataFrame(results)

    if not df.empty:
        table = tabulate(
            df, headers="keys", maxcolwidths=[None, 60, 60], tablefmt="grid"
        )
        print(table)
    else:
        logger.warning("No files found or processed in the uploads directory.")


# Example usage
if __name__ == "__main__":
    try:
        process_all_documents("./private_test_data")
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {str(e)}")
