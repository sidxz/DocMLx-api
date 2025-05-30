from typing import List
from langchain_core.documents import Document
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.llm import LanguageModel
from app.core.logging_config import logger
from app.service.lm.generic.correctors.context_filter import summary_context_filter
import pandas as pd
from tabulate import tabulate


def summarize_slide(slide_content: str) -> str:
    """
    Summarizes the content of a slide.

    Args:
        slide_content (str): The text content of the slide.

    Returns:
        str: The summarized content of the slide or an "Unknown" message if an error occurs.
    """
    logger.debug("Starting slide summarization.")

    try:
        # Initialize the language model and output parser
        parser = StrOutputParser()
        # prompt_template = PromptTemplate(
        #     template="""
        #     Provide a concise summary of the Slide in a paragraph, the Slide related to the field of TB drug discovery.
        #     Maintain the original ideas, pick important lines, and avoid drawing any conclusions.
        #     Include exceptions or negative results, and retain numerical values as is.
        #     Only summarize content from the Slide, do not add additional context or information that is not in the slide.
        #     Output only the Summary and do NOT include any introductory statements, explanations, or additional text.

        #     Slide: {slide}
        #     Summary:
        #     """,
        #     input_variables=["slide"],
        # )
#         prompt_template = PromptTemplate(
#     template="""
#     Carefully read the provided Slide and generate a concise summary in one paragraph. The Slide is related to the field of TB drug discovery.
#     The summary must strictly adhere to the content of the Slide, only rephrasing or condensing ideas directly present in the text. 
#     Do not infer, interpret, or add any information not explicitly found in the Slide. 
#     Retain all numerical values as presented and include exceptions or negative results where applicable. 
#     Avoid drawing conclusions, synthesizing data, or incorporating outside knowledge.

#     Important: The output must be a factual summary strictly based on the Slide. 
#     Do not include introductory statements, explanations, or any additional text.

#     Slide: {slide}

#     Summary: <your response>
#     """,
#     input_variables=["slide"],
# )

        prompt_template = PromptTemplate(
            template="""
            Carefully read the provided Slide text related to TB drug discovery. Generate a concise, one-paragraph summary.

            The summary must *strictly* adhere to the content of the Slide text, rephrasing or condensing ideas directly present. Do not infer, interpret, or add any information not explicitly found in the
            Slide.

            **Regarding numerical data:**  Retain numerical values *as they appear in the Slide text*. If a number seems potentially inaccurate due to OCR errors or unclear presentation (e.g., a table is poorly
            formatted), *describe the value generally rather than using the specific number*.  For example, instead of "The efficacy was 2.3%", say "The efficacy was reported as a low percentage" or "The
            efficacy was reported in the low single digits".  Include exceptions or negative results where applicable.

            Avoid drawing conclusions, synthesizing data, or incorporating outside knowledge.  Focus on *what is stated* in the text, not *what it means*.

            Important: The output must be a factual summary strictly based on the Slide text. Do not include introductory statements, explanations, or any additional text.

            Slide: {slide}

            Summary: <your response>
            """,
            input_variables=["slide"],
        )


        # Initialize the language model instance
        lm_instance = LanguageModel(model_type="ChatOllama")
        llm = lm_instance.get_llm()

        # Create the summary chain using the prompt and the language model
        summary_chain = prompt_template | llm | parser

        # Invoke the chain with the provided document content
        summary_response = summary_chain.invoke({"slide": slide_content})
        logger.info(f"Summary generated for the slide: {summary_response}")
        return summary_response

    except ValueError as ve:
        logger.error(f"Validation error: {ve}")
        return "Invalid slide content."
    except ConnectionError as ce:
        logger.error(f"Connection error while accessing the language model: {ce}")
        return "Connection error. Try again later."
    except Exception as e:
        logger.error("An error occurred during slide summarization.", exc_info=True)
        return "Unknown"


def create_summary_list(
    documents: List[Document],
    apply_context_filter: bool = True,
    min_content_length: int = 200,
) -> List[str]:
    """
    Creates a summary list of the content of the slides in a presentation.

    Args:
        documents (List[Document]): A list of Document objects representing the slides in a presentation.
        apply_context_filter (bool): Whether to apply the context filter to the summaries. Defaults to True.
        min_content_length (int): Minimum length of content required for summarization. Defaults to 200.

    Returns:
        List[str]: A list of summarized content of the slides.
    """
    summary_list = []
    summary_df = pd.DataFrame(
        columns=["Slide Number", "Original Content", "Summary", "Filtered Summary"]
    )

    for i, slide in enumerate(documents, start=1):
        logger.info(f"Processing slide {i}")

        try:
            slide_content = slide.page_content

            # Skip summarization if the content is too short
            if len(slide_content) >= min_content_length:

                summary = summarize_slide(slide_content)
            else:
                logger.debug(
                    f"Skipping summarization for slide {i}: content length {len(slide_content)} is below the minimum of {min_content_length}."
                )
                summary = slide_content

            # Apply context filter if enabled
            if apply_context_filter and len(slide_content) >= min_content_length:
                filtered_summary = summary_context_filter(slide_content, summary)
            else:
                filtered_summary = summary

            # Append summaries to list and dataframe
            summary_list.append(filtered_summary)
            summary_df.loc[i] = [i, slide_content, summary, filtered_summary]

        except TypeError as te:
            logger.error(f"Type error with slide {i}: {te}")
            summary_list.append("Invalid document type.")
        except Exception as e:
            logger.error(f"Error summarizing slide {i}: {e}", exc_info=True)
            summary_list.append("Error during summarization")

    # Display the summaries in a tabular format if the DataFrame is not empty
    if not summary_df.empty:
        table = tabulate(
            summary_df,
            headers="keys",
            maxcolwidths=[None, 1, 40, 40, 40],
            tablefmt="grid",
        )
        logger.info(f"Summary table for presentation:\n{table}")

    return summary_list
