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


def summarize_slide(text_content: str, img_content: BytesIO) -> str:
    logger.debug("Starting slide summarization in hybrid mode.")

    # Step 1: Preprocess the image
    try:
        image = Image.open(img_content)

        # Preprocess image for LLM (enhance clarity, format for input)
        image = preprocess_img_for_llm(
            image, enhance_contrast=True, sharpen=True, resize=True, denoise=True
        )

        img_base64 = image_to_base64(image)
    except Exception as e:
        logger.error("Image preprocessing failed.", exc_info=True)
        return "Unknown"

    # Step 2: Construct hybrid prompt
    try:
        hybrid_multimodal_prompt = PromptTemplate(
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

            Parsed Text:
            {parsed_text}

            Summary:
            """,
        )

        formatted_prompt = hybrid_multimodal_prompt.format(parsed_text=text_content)

        # Step 3: Initialize the language model and query with image
        lm_instance = LanguageModel(model_type="ChatOllama")
        summary = lm_instance.query_with_image(
            prompt=formatted_prompt, image_base64=img_base64
        )

        logger.info(f"Summary generated for the slide: {summary}")
        return summary

    # Step 4: Error handling
    except ValueError as ve:
        logger.error("Validation error encountered.", exc_info=True)
        return "Invalid slide content."
    except ConnectionError as ce:
        logger.error(
            "Connection error while accessing the language model.", exc_info=True
        )
        return "Connection error. Try again later."
    except Exception as e:
        logger.error("Unexpected error during slide summarization.", exc_info=True)
        return "Unknown"


def create_summary_list(
    text_documents: List[Document],
    img_documents: List[BytesIO],
    apply_context_filter: bool = True,
) -> List[str]:

    summary_list = []
    summary_df = pd.DataFrame(
        columns=["Slide Number", "Original Content", "Summary", "Filtered Summary"]
    )

    for idx, (text_doc, img_doc) in enumerate(
        zip(text_documents, img_documents), start=1
    ):
        try:
            logger.info(f"Processing slide {idx}...")

            # Validate inputs
            if not isinstance(text_doc, Document) or not hasattr(
                text_doc, "page_content"
            ):
                raise TypeError("Invalid text document structure.")
            if not hasattr(img_doc, "read"):
                raise TypeError("Image document must be a BytesIO-like object.")

            # Generate summary
            summary = summarize_slide(text_doc.page_content, img_doc)

            # Optional context filter (if implemented later)
            filtered_summary = summary  # Placeholder if future filtering is applied

            # Append to list and log summary
            summary_list.append(filtered_summary)

            summary_df.loc[idx] = [
                idx,
                text_doc.page_content,
                summary,
                filtered_summary,
            ]

        except TypeError as te:
            logger.error(f"Type error on slide {idx}: {te}")
            summary_list.append("Invalid document type.")
        except Exception as e:
            logger.error(f"Unexpected error on slide {idx}: {e}", exc_info=True)
            summary_list.append("Error during summarization.")

    # Display final summary table if any summaries exist
    if not summary_df.empty:
        table = tabulate(
            summary_df,
            headers="keys",
            maxcolwidths=[None, 40, 40, 40],
            tablefmt="grid",
        )
        logger.info(f"Summary Table:\n{table}")

    return summary_list
