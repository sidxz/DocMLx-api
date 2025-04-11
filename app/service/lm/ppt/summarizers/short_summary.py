from typing import List
from langchain_core.documents import Document
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.llm import LanguageModel
from app.core.logging_config import logger
from app.service.lm.generic.correctors.context_filter import summary_context_filter
import pandas as pd
from tabulate import tabulate

def generate_short_summary(content: List[str]) -> str:
    """
    Summarizes the content

    Args:
        content: The list of text content of the slides.

    Returns:
        str: The summarized content of the slide or an "Unknown" message if an error occurs.
    """
    logger.debug("Starting short summarization.")

    contents = " ".join(content)  # Join the list of strings into a single string
    if contents.strip() == "":
        return "Summary not available."

    try:
        # Initialize the language model and output parser
        parser = StrOutputParser()
        prompt_template = PromptTemplate(
            template="""
    Using the provided content, create a concise and cohesive summary in a single paragraph strictly limited to 5 lines. 
    The summary should consist only of complete sentences, without any bullet points or lists. 
    Retain all numerical values as they appear and ensure the information is accurate and directly based on the content. 
    Do not include any introductions, explanations, or extraneous text beyond the summary itself.

    Content: {content}

    Summary: <Your Response>
    """,
            input_variables=["content"],
        )

        # Initialize the language model instance
        lm_instance = LanguageModel(model_type="ChatOllama")
        llm = lm_instance.get_llm()

        # Create the summary chain using the prompt and the language model
        summary_chain = prompt_template | llm | parser
        logger.debug("___________________________SHORT SUMMARY___________________________")
        # Invoke the chain with the provided document content
        summary_response = summary_chain.invoke({"content": contents})
        logger.info(f"{summary_response}")
        logger.debug("___________________________END SHORT SUMMARY___________________________")
        return summary_response

    except ValueError as ve:
        logger.error(f"Validation error: {ve}")
        return "Invalid content."
    except ConnectionError as ce:
        logger.error(f"Connection error while accessing the language model: {ce}")
        return "Connection error. Try again later."
    except Exception as e:
        logger.error("An error occurred during summarization.", exc_info=True)
        return "Unknown"
    

def filter_bullets_summary(content: str) -> str:
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
            If the provided summary contains bullet points or lists, detect and transform them into a cohesive paragraph. 
            Ensure the paragraph consists of complete sentences and conveys the same meaning as the original summary. 
            If no bullet points or lists are present, return the input summary unchanged. 
            Limit the paragraph to 150 words, prioritizing clarity and conciseness. 
            Retain all numerical values and maintain factual accuracy without adding new information.
            Do not include any introductions, explanations, or extraneous text beyond the summary itself.

            Summary:
            {summary}

            Paragraph (150 words max): <Your Response>
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
        
        logger.debug("___________________________FILTERED SUMMARY___________________________")
        # Invoke the chain with the provided document content
        logger.info(f"{resummary_response}")
        logger.debug("___________________________END FILTERED SUMMARY___________________________")

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
        
        logger.debug("___________________________SHORTEN SUMMARY___________________________")
        # Invoke the chain with the provided document content
        logger.info(f"{resummary_response}")
        logger.debug("___________________________END SHORTEN SUMMARY___________________________")

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