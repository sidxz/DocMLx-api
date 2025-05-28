import os
import sys
import random
import textwrap



# Add the parent directory to the system path for module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.service.doc_loader.pdf_loader import load_pdf_document
from app.core.logging_config import logger
from app.service.lm.ppt.summarizers.short_summary import filter_bullets_summary, generate_short_summary
from app.service.doc_loader.pdf_to_img_loader import pdf_to_png_byte_streams
from app.service.lm.ppt.hybrid_summarizers.slide_summary import create_summary_list
from app.utils.text_processing import contains_bullet_points, count_words_nltk

def test_create_summary_list(upload_dir: str):
    """
    Tests the create_summary_list function by processing a randomly selected file
    from the specified directory. The output is presented in a tabular format using pandas.

    Args:
        upload_dir (str): The directory containing the documents.
    """
    if not os.path.isdir(upload_dir):
        logger.error(
            f"The provided directory '{upload_dir}' does not exist or is not a directory."
        )
        return

    # Get all files in the uploads directory
    files = [
        f for f in os.listdir(upload_dir) if os.path.isfile(os.path.join(upload_dir, f))
    ]
    if not files:
        logger.warning("No files found in the uploads directory.")
        return

    # Randomly select a file
    random_file = random.choice(files)
    file_location = os.path.join(upload_dir, random_file)
    # file_location = os.path.join(upload_dir, "04_2021-10-05_Bates_GSK Screens_v1.pdf")

    logger.debug(f"Processing randomly selected file: {random_file}")
    try:
        # Load the document
        pdf_doc = load_pdf_document(file_location)
        img_doc = pdf_to_png_byte_streams(file_location)
        # Generate summaries for each slide in the document

        summaries = create_summary_list(
            text_documents=pdf_doc.loaded_docs, img_documents=img_doc
        )

        # Prepare results for the table
        results = [
            {
                "Original Content": slide.page_content,
                "Summary": summary,
            }
            for i, (slide, summary) in enumerate(zip(pdf_doc.loaded_docs, summaries))
        ]

    except Exception as e:
        # Log any error encountered during file processing
        logger.error(f"Error processing file '{random_file}': {str(e)}")

    # Display a overall short summary
    try:
        short_summary = generate_short_summary(summaries)
        wrapped_summary = textwrap.fill(short_summary, width=100)
        print("\n" + "-" * 102)
        print("|{:^100}|".format("SHORT SUMMARY"))
        print("-" * 102)
        for line in wrapped_summary.split("\n"):
            print(f"| {line:<98} |")
        print("-" * 102)
        
        bullets_present = contains_bullet_points (short_summary)
        if bullets_present:
            
            logger.info("Bullet points detected in the summary.")
            short_summary = filter_bullets_summary(short_summary)
        
        
        no_of_words = count_words_nltk(short_summary)
        logger.info(f"Number of words in the summary: {no_of_words}")   

    except Exception as e:
        logger.error(f"Error generating short summary: {str(e)}")


# Example usage
if __name__ == "__main__":
    try:
        test_create_summary_list("./private_test_data")
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {str(e)}")
