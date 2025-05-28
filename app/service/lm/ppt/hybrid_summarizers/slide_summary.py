from io import BytesIO
from typing import List
import pandas as pd
from tabulate import tabulate
from PIL import Image

from app.core.llm import LanguageModel
from app.core.logging_config import logger
from langchain.prompts import PromptTemplate

from app.schema.results.document import Document
from app.utils.img_processing import image_to_base64, preprocess_img_for_llm
from app.utils.slide_categorization import is_backup_slide

"""
/*
 * Function: summarize_slide_from_image_and_text
 * ---------------------------------------------
 * Generates a one-paragraph summary using both OCR text and an image of the slide.
 *
 * Parameters:
 *   text_content (str)     - Extracted text from OCR.
 *   img_content (BytesIO)  - Binary image data.
 *   prev_slides (List[str])- Summaries of the previous two slides (optional).
 *
 * Returns:
 *   str - A factual summary or fallback error message.
 */
"""


def summarize_slide_from_image_and_text(
    text_content: str, img_content, prev_slides: List[str] = []
) -> str:
    logger.debug("Starting slide summarization in hybrid mode.")

    try:
        # Open and preprocess image
        image = Image.open(img_content)
        processed_image = preprocess_img_for_llm(
            image, enhance_contrast=True, sharpen=True, resize=True, denoise=True
        )
        img_base64 = image_to_base64(processed_image)
    except Exception as e:
        logger.error("Image preprocessing failed.", exc_info=True)
        return "Unknown"

    prev_slides_str = "\n".join(slide.strip() for slide in prev_slides if slide.strip())

    try:
        # Construct the hybrid prompt
        hybrid_prompt = PromptTemplate(
            input_variables=["parsed_text", "prev_slides"],
            template="""
            I want to write a concise paragraph of three to four lines that summarizes a slide related to tuberculosis (TB) drug discovery.
            Help me write it following the instructions.

            I have access to:
            - An image of the slide that preserves layout, tables, and figures.
            - Parsed text content extracted from the slide, which may contain errors or formatting issues.
            - The content of the previous two slides, for context only.

            Instructions:
            - Always Prioritize information visible in the image of the slide for summarization, especially if they are in bold/highlighted.
            - Use the parsed text content only when parts of the image are unreadable or unclear. (Image takes precedence in graphs and tables)
            - Use the content of previous two slides only for context. Do not include this in summary.
            - Never infer or interpret beyond what's explicitly visible in the image or stated in the text.
            - Never include raw data or reporting of numbers in summary. The goal is to capture a high level gist without being too technical.
            - Never draw conclusions.
            - Do not expand acronyms, abbreviations, or short forms — use them exactly as shown.
            - Do not include introductory phrases
            - Prefer the language used in the slide
            - Try capturing the heading of the slide in the summary as is.

            Important:
            My summary should be strictly factual, based only on the image of the slide or the text content.
            I should be extremely cautious when using the parsed text content and must cross-verify it with the image to ensure accuracy.
            If there is no input, say "No Input"

            Parsed Text:
            {parsed_text}


            Content of Previous Two Slides:
            {prev_slides}
            
            Summary: <Your Response>
            """,
        )

        formatted_prompt = hybrid_prompt.format(
            parsed_text=text_content, prev_slides=prev_slides_str
        )

        # Query the LLM with both text and image
        llm = LanguageModel(model_type="ChatOllama")
        summary = llm.query_with_image(prompt=formatted_prompt, image_base64=img_base64)

        logger.info(f"Slide summary generated successfully: {summary}")
        return summary

    except ValueError:
        logger.error(
            "Validation error encountered during summarization.", exc_info=True
        )
        return "Invalid slide content."
    except ConnectionError:
        logger.error(
            "Connection error while querying the language model.", exc_info=True
        )
        return "Connection error. Try again later."
    except Exception as e:
        logger.error("Unexpected error during slide summarization. {e}", exc_info=True)
        return "Unknown"


"""
/*
 * Function: summarize_slide_from_image
 * ------------------------------------
 * Generates a summary using only the image and context from previous slides.
 *
 * Parameters:
 *   img_content (BytesIO)   - Slide image data.
 *   prev_slides (List[str]) - Previous two slide summaries.
 *
 * Returns:
 *   str - Summary or fallback error string.
 */
"""


def summarize_slide_from_image(img_content, prev_slides: List[str] = []) -> str:
    logger.debug("Starting slide summarization in image only mode.")

    try:
        # Open and preprocess image
        image = Image.open(img_content)
        processed_image = preprocess_img_for_llm(
            image, enhance_contrast=True, sharpen=True, resize=True, denoise=True
        )
        img_base64 = image_to_base64(processed_image)
    except Exception as e:
        logger.error("Image preprocessing failed.", exc_info=True)
        return "Unknown"

    prev_slides_str = "\n".join(slide.strip() for slide in prev_slides if slide.strip())

    try:
        # Construct the hybrid prompt
        hybrid_prompt = PromptTemplate(
            input_variables=["prev_slides"],
            template="""
                I want to write a concise paragraph of two to three lines that summarizes a slide related to tuberculosis (TB) drug discovery.
                Please follow these exact instructions.
            
                Available Inputs:
                - An image of the slide, preserving layout, tables, and figures.
                - The content of the previous two slides, for context only.
            
                Instructions:
                - Always prioritize information visibly present in the slide image, especially bolded or highlighted text.
                - Use the Content of Previous Two Slides only to understand context — do not include their content in the summary.
                - Never infer or interpret beyond what's explicitly shown in the image.
                - Never include raw data or reporting of numbers in summary. The goal is to capture a high level gist without being too technical.
                - Never draw conclusions or assumptions.
                - Do not expand acronyms, abbreviations, or short forms — preserve them as shown.
                - Avoid introductory phrases like "This slide shows..." or "The figure illustrates...".
                - Prefer reusing the language used in the slide.
                - Keep the summary strictly factual, grounded only in the slide image content.
                - Try capturing the heading of the slide in the summary as is.

            
                If there is no slide content available, respond with: "No Input"
            
                ---
                Content of Previous Two Slides:
                {prev_slides}
            
                ---
                Summary: <Your Response>
            """,
        )

        formatted_prompt = hybrid_prompt.format(prev_slides=prev_slides_str)

        # Query the LLM with both text and image
        llm = LanguageModel(model_type="ChatOllama")
        summary = llm.query_with_image(prompt=formatted_prompt, image_base64=img_base64)

        logger.info(f"Slide summary generated successfully: {summary}")
        return summary

    except ValueError:
        logger.error(
            "Validation error encountered during summarization.", exc_info=True
        )
        return "Invalid slide content."
    except ConnectionError:
        logger.error(
            "Connection error while querying the language model.", exc_info=True
        )
        return "Connection error. Try again later."
    except Exception as e:
        logger.error(f"Unexpected error during slide summarization. {e}", exc_info=True)
        return "Unknown"


"""
/*
 * Function: create_summary_list
 * -----------------------------
 * Batch generates slide summaries using OCR text and image data.
 *
 * Parameters:
 *   text_documents (List[Document])  - Parsed text documents.
 *   img_documents (List[BytesIO])    - Corresponding slide images.
 *   apply_context_filter (bool)      - Flag to apply summary filtering logic.
 *   min_content_length (int)         - Text threshold to decide mode.
 *
 * Returns:
 *   List[str] - Summaries or error messages per slide.
 */
"""


def create_summary_list(
    text_documents: List[Document],
    img_documents: List[BytesIO],
    apply_context_filter: bool = True,
    min_content_length: int = 100,
) -> List[str]:
    summary_list = []
    table_rows = []

    for idx, (text_doc, img_doc) in enumerate(
        zip(text_documents, img_documents), start=0
    ):
        try:
            # Gather previous 2 summaries if they exist
            prev_slides = []
            if idx - 2 >= 0:
                prev_slides.append(summary_list[idx - 2])
            if idx - 1 >= 0:
                prev_slides.append(summary_list[idx - 1])

            content_length = len(text_doc.page_content)
            
            # Check if this slide is a backup slide
            is_backup = is_backup_slide(text_doc.page_content, img_doc)
            if is_backup.strip().lower() == "true":
                logger.info("Backup slide detected. Stopping further processing.")
                break

            if content_length >= min_content_length:
                logger.info(f"Processing slide {idx}...")

                summary = summarize_slide_from_image_and_text(
                    text_doc.page_content, img_doc, prev_slides=prev_slides
                )

                if apply_context_filter:
                    # TODO: Apply content filtering logic here if needed
                    filtered_summary = summary
                else:
                    filtered_summary = summary

            else:
                # Generate summary
                summary = summarize_slide_from_image(
                    img_content=img_doc, prev_slides=prev_slides
                )

                # Optional context filter (not yet used)
                filtered_summary = summary

            # Log the summary
            summary_list.append(filtered_summary)
            table_rows.append([idx, filtered_summary])

        except TypeError as te:
            logger.error(f"Type error on slide {idx}: {te}")
            summary_list.append("Invalid document type.")
            table_rows.append([idx, "Invalid document type."])
        except Exception as e:
            logger.error(f"Unexpected error on slide {idx}. {e}", exc_info=True)
            summary_list.append("Error during summarization.")
            table_rows.append([idx, "Error during summarization."])

    # Print summary table to console
    if table_rows:
        print("\n" + "-" * 50)
        print("|{:^96}|".format("SLIDE SUMMARIES"))
        print("-" * 50)
        table = tabulate(
            table_rows, headers=["Slide Number", "Summary"], tablefmt="grid"
        )
        print(table)

    return summary_list
