from typing import List
from langchain_core.documents import Document
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.llm import LanguageModel
from app.core.logging_config import logger
from app.service.lm.generic.correctors.context_filter import summary_context_filter
import pandas as pd
from tabulate import tabulate

"""
/*
 * Function: generate_short_summary
 * -------------------------------
 * Generates a concise {len}-sentence paragraph summarizing key points from slide content.
 *
 * Parameters:
 *   content (List[str]) - A list of strings where each element represents the content of a slide.
 *
 * Returns:
 *   str - A final summarized paragraph or an appropriate error message in case of failure.
 *
 * Notes:
 *   - Content is summarized in batches of {batch_size} slides to manage LLM prompt size.
 *   - Final summary is generated from batch summaries if multiple batches exist.
 *   - Exceptions are caught and logged to avoid leaking sensitive info.
 */
"""


def generate_short_summary(
    content: List[str], max_summary_sentences: int = 10, batch_size: int = 15
) -> str:
    logger.debug("Starting short summarization.")

    # Validate input
    if not content or all(not slide.strip() for slide in content):
        logger.warning("Empty or invalid content provided.")
        return "Summary not available."

    try:
        # Prompt for summarization with strict formatting and inclusion rules
        prompt_template = PromptTemplate(
            template="""
You are given a collection of slide-level summaries from a tuberculosis drug discovery research presentation.

Your task is to extract and compile the most important takeaways into a single, coherent paragraph of exactly {len} complete sentences.
If mentioned, capture Mtb target name.

Requirements:
Do not mention that this is a TB drug discovery program — the audience already knows this.
Limit the text to a single paragraph, no more than {len} lines.
Condense by selection, not by synthesis. i.e Condense by selecting key points, not by generating new interpretations or rephrasing into novel insights
Use only complete, factual sentences grounded in the content provided.
Do not use bullet points, lists, headings, or introductory phrases like "In summary."
Do not add interpretations, background, or conclusions beyond the provided text.

Important: Your output should only include the final paragraph. Do not include any explanations, instructions, or formatting beyond the paragraph.
Content:
{content}

Summary:
            """,
            input_variables=["content", "len"],
        )

        # Initialize components
        output_parser = StrOutputParser()
        llm = LanguageModel(model_type="ChatOllama").get_llm()
        summary_chain = prompt_template | llm | output_parser

        # Break content into manageable batches
        BATCH_SIZE = batch_size
        batch_summaries = []

        for batch_index in range(0, len(content), BATCH_SIZE):
            batch = content[batch_index : batch_index + BATCH_SIZE]
            cleaned_batch = "\n".join(slide.strip() for slide in batch if slide.strip())

            logger.info(
                f"--- BATCH {batch_index // BATCH_SIZE + 1} CONTENT ---\n{cleaned_batch}"
            )

            SUMMARY_LENGTH = str(min(len(batch), max_summary_sentences))

            summary = summary_chain.invoke(
                {"content": cleaned_batch, "len": SUMMARY_LENGTH}
            )
            logger.info(
                f"--- BATCH {batch_index // BATCH_SIZE + 1} SUMMARY ---\n{summary}"
            )

            batch_summaries.append(summary)

        # Final summary generation
        if len(batch_summaries) == 1:
            final_summary = batch_summaries[0]
        else:
            combined_summary = "\n".join(batch_summaries)
            SUMMARY_LENGTH = str(max_summary_sentences)
            final_summary = summary_chain.invoke(
                {"content": combined_summary, "len": SUMMARY_LENGTH}
            )

        logger.info("--- FINAL SUMMARY ---")
        logger.info(final_summary)

        logger.debug("Completed short summarization successfully.")
        return final_summary

    except ValueError as validation_error:
        logger.error(f"Validation error: {validation_error}")
        return "Invalid content."
    except ConnectionError as connection_error:
        logger.error(
            f"Connection error while accessing the language model: {connection_error}"
        )
        return "Connection error. Try again later."
    except Exception as unexpected_error:
        logger.exception("Unexpected error occurred during summarization.")
        return "Unknown"


def filter_bullets_summary(content: str, summary_length: str = "ten") -> str:
    """
    Refactor a given summary into a concise paragraph, maintaining clarity, accuracy, and coherence.

    Parameters:
        content (str): The input summary to process.

    Returns:
        str: The resummarized content or an appropriate error message.
    """
    logger.debug("Starting the filter_bullets_summary process.")

    if not content.strip():
        logger.warning("Empty content provided for resummarization.")
        return "Summary not available."

    try:
        # Validate and preprocess input
        trimmed_content = content.strip()

        # Initialize parser and prompt template
        parser = StrOutputParser()

        prompt_template = PromptTemplate(
            template="""
            If the provided summary contains bullet points or lists, detect and transform them into a cohesive paragraph of exactly {len} complete sentences. 
            Ensure the paragraph consists of complete sentences and conveys the same meaning as the original summary. 
            If no bullet points or lists are present, return the input summary unchanged. 
            
            Requirements:
            Do not mention that this is a TB drug discovery program — the audience already knows this.
            Limit the text to a single paragraph, no more than {len} lines.
            Condense by selection, not by synthesis. i.e Condense by selecting key points, not by generating new interpretations or rephrasing into novel insights
            Use only complete, factual sentences grounded in the content provided.
            Do not use bullet points, lists, headings, or introductory phrases like "In summary."
            Do not add interpretations, background, or conclusions beyond the provided text.

            Important: Your output should only include the final paragraph. Do not include any explanations, instructions, or formatting beyond the paragraph.

            Summary:
            {summary}

            Paragraph ({len} lines max): <Your Response>
            """,
            input_variables=["summary", "len"],
        )

        SUMMARY_LENGTH = summary_length

        # Initialize the language model
        lm_instance = LanguageModel(model_type="ChatOllama")
        llm = lm_instance.get_llm()

        # Create the resummarization chain
        resummary_chain = prompt_template | llm | parser

        # Invoke the chain with the provided content
        resummary_response = resummary_chain.invoke(
            {"summary": trimmed_content, "len": SUMMARY_LENGTH}
        )

        logger.debug(
            "___________________________FILTERED SUMMARY___________________________"
        )
        # Invoke the chain with the provided document content
        logger.info(f"{resummary_response}")
        logger.debug(
            "___________________________END FILTERED SUMMARY___________________________"
        )

        return resummary_response

    except ValueError as ve:
        logger.error(f"Validation error during filter_bullets_summary: {ve}")
        return "Invalid content provided. Please check your input."
    except ConnectionError as ce:
        logger.error(f"Connection error with the language model: {ce}")
        return "Connection error. Please try again later."
    except Exception as e:
        logger.exception("An unexpected error occurred during filter_bullets_summary.")
        return "An unexpected error occurred. Please try again later."


def shorten_summary(content: str) -> str:
    """
    Refactor a given summary into a concise paragraph, maintaining clarity, accuracy, and coherence.

    Parameters:
        content (str): The input summary to process.

    Returns:
        str: The resummarized content or an appropriate error message.
    """
    logger.debug("Starting the shorten summary process.")

    if not content.strip():
        logger.warning("Empty content provided for resummarization.")
        return "Summary not available."

    try:
        # Validate and preprocess input
        trimmed_content = content.strip()

        # Initialize parser and prompt template
        parser = StrOutputParser()

        prompt_template = PromptTemplate(
            template="""
    Shorten the provided summary to 150 words or fewer while ensuring it remains a cohesive and concise paragraph. 
    The output must consist of complete sentences, avoiding bullet points, lists, or headings. 
    Retain the original meaning, key details, and numerical values as they appear, ensuring factual accuracy. 
    Do not add new information or make assumptions. Focus on summarizing the most important points clearly and concisely.
    Do not include any introductions, explanations, or extraneous text beyond the summary itself.

    Summary:
    {summary}

    Shortened Paragraph (150 words max): <Your Response>
    """,
            input_variables=["summary"],
        )

        # Initialize the language model
        lm_instance = LanguageModel(model_type="ChatOllama")
        llm = lm_instance.get_llm()

        # Create the resummarization chain
        resummary_chain = prompt_template | llm | parser

        # Invoke the chain with the provided content
        resummary_response = resummary_chain.invoke({"summary": trimmed_content})

        logger.debug(
            "___________________________SHORTEN SUMMARY___________________________"
        )
        # Invoke the chain with the provided document content
        logger.info(f"{resummary_response}")
        logger.debug(
            "___________________________END SHORTEN SUMMARY___________________________"
        )

        return resummary_response

    except ValueError as ve:
        logger.error(f"Validation error during shorten summary: {ve}")
        return "Invalid content provided. Please check your input."
    except ConnectionError as ce:
        logger.error(f"Connection error with the language model: {ce}")
        return "Connection error. Please try again later."
    except Exception as e:
        logger.exception("An unexpected error occurred during shorten summary.")
        return "An unexpected error occurred. Please try again later."
