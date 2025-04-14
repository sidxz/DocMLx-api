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

"""
/*
 * Function: summarize_slide
 * -------------------------
 * Generates a concise one-paragraph summary of a slide using both text content and an image.
 *
 * Parameters:
 *   text_content (str)   - Extracted OCR/parsed text from the slide.
 *   img_content (BytesIO) - Raw binary image data of the slide.
 *
 * Returns:
 *   str - A factual one-paragraph summary or an error message.
 */
"""


def summarize_slide(text_content: str, img_content: BytesIO) -> str:
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

    try:
        # Construct the hybrid multimodal prompt
        hybrid_prompt = PromptTemplate(
            input_variables=["parsed_text"],
            template="""
You are presented with a scientific slide related to TB drug discovery.
Your job is to generate a concise, one-paragraph summary.

You have access to:
- An **image of the slide** that preserves layout, tables, and figures.
- Parsed **text content** extracted from the slide, which may contain errors or formatting issues.

**Instructions**:
- Prioritize information visible in the **image of the slide** for summarization.
- Use the parsed text content only when parts of the image are unreadable or unclear.
- Do not infer or interpret beyond what's explicitly visible in the image or stated in the text.
- Avoid detailed reporting of raw numbers from tables or charts if they are not clear. 
- Avoid using external knowledge or drawing conclusions.
- Do not include introductory phrases
- Prefer the language used in the slide

Write a concise, factual, one-paragraph summary of the slide with the key takeaways.
If there is no input, say "No Input"
Parsed Text:
{parsed_text}

Summary:
            """,
        )

        formatted_prompt = hybrid_prompt.format(parsed_text=text_content)

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
    except Exception:
        logger.error("Unexpected error during slide summarization.", exc_info=True)
        return "Unknown"


"""
/*
 * Function: create_summary_list
 * -----------------------------
 * Generates a list of slide summaries using OCR text and image content.
 *
 * Parameters:
 *   text_documents (List[Document])  - List of parsed text documents for each slide.
 *   img_documents (List[BytesIO])    - Corresponding image data for each slide.
 *   apply_context_filter (bool)      - Optional context-based filtering of output summaries.
 *   min_content_length (int)         - Threshold below which summarization is skipped.
 *
 * Returns:
 *   List[str] - A list of summaries or fallback messages per slide.
 */
"""


def create_summary_list(
    text_documents: List[Document],
    img_documents: List[BytesIO],
    apply_context_filter: bool = True,
    min_content_length: int = 20,
) -> List[str]:
    summary_list = []
    table_rows = []

    for idx, (text_doc, img_doc) in enumerate(
        zip(text_documents, img_documents), start=1
    ):
        try:
            text = text_doc.page_content

            if len(text) >= min_content_length:
                logger.info(f"Processing slide {idx}...")

                summary = summarize_slide(text, img_doc)

                if apply_context_filter:
                    # TODO: Apply content filtering logic here if needed
                    filtered_summary = summary
                else:
                    filtered_summary = summary

                summary_list.append(filtered_summary)
                table_rows.append([idx, filtered_summary])
            else:
                logger.info(
                    f"Skipping summarization for slide {idx}: "
                    f"Content length ({len(text)}) is below threshold ({min_content_length})."
                )
                summary_list.append(text)
                table_rows.append([idx, text])

        except TypeError as te:
            logger.error(f"Type error on slide {idx}: {te}")
            summary_list.append("Invalid document type.")
            table_rows.append([idx, "Invalid document type."])
        except Exception as e:
            logger.error(f"Unexpected error on slide {idx}.", exc_info=True)
            summary_list.append("Error during summarization.")
            table_rows.append([idx, "Error during summarization."])

    # Print summary table to console
    if table_rows:
        print("\n" + "-" * 100)
        print("|{:^96}|".format("SLIDE SUMMARIES"))
        print("-" * 100)
        table = tabulate(
            table_rows, headers=["Slide Number", "Summary"], tablefmt="grid"
        )
        print(table)

    return summary_list
