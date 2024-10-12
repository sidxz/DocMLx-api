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
        prompt_template = PromptTemplate(
            template="""
            Provide a concise summary of the Slide in a paragraph, the Slide is most likely related to the field of TB drug discovery. 

            Maintain the original ideas, and pick important lines, and avoid drawing any conclusions. 
            If mentioned be sure to include exceptions/ negative results.
            If any stages of drug discovery are mentioned (e.g., screening, H2L, LO, SP, IND, P1), include them as they appear. 
            Retain any dates, calculations, or numerical values without altering or interpreting them.

            Only include content from the Slide, do not generate any additional context/ideas; Sentence formatting is okay.
            If the paragraph contains no relevant information, return an empty response.

            Important: Output only the summary directly without any introductory statements, explanations, or additional text.

            Slide: {slide}
            Summary:
            """,
            input_variables=["slide"],
        )

        # Initialize the language model instance
        lm_instance = LanguageModel(type="ChatOllama")
        llm = lm_instance.get_llm()

        # Create the summary chain using the prompt and the language model
        summary_chain = prompt_template | llm | parser

        # Invoke the chain with the provided document content
        summary_response = summary_chain.invoke({"slide": slide_content})
        logger.info(f"Slide Content: {slide_content}")
        logger.info(f"Summary: {summary_response}")
        return summary_response

    except Exception as e:
        logger.error("An error occurred during slide summarization.", exc_info=True)
        return "Unknown"


def create_summary_list(
    documents: List[Document], apply_context_filter: bool = True
) -> List[str]:
    """
    Creates a summary list of the content of the slides in a presentation.

    Args:
        documents (List[Document]): A list of Document objects representing the slides in a presentation.
        apply_context_filter (bool): Whether to apply the context filter to the summaries. Defaults to True.

    Returns:
        List[str]: A list of summarized content of the slides.
    """
    summary_list = []
    summary_df = pd.DataFrame(
        columns=["Slide Number", "Original Content", "Summary", "Filtered Summary"]
    )

    for i, slide in enumerate(documents, start=1):
        logger.info(f"Summarizing slide: {i}")
        try:
            # Summarize the slide content
            summary = summarize_slide(slide.page_content)

            if apply_context_filter:
                filtered_summary = summary_context_filter(slide.page_content, summary)
                summary_list.append(filtered_summary)
                summary_df.loc[i] = [
                    i,
                    slide.page_content,
                    summary,
                    filtered_summary,
                ]
            else:
                summary_list.append(summary)
                summary_df.loc[i] = [
                    i,
                    slide.page_content,
                    summary,
                    "",
                ]

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
        print(table)

    return summary_list
