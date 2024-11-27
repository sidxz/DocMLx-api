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
    logger.debug("Starting slide summarization.")

    contents = " ".join(content)  # Join the list of strings into a single string
    if contents.strip() == "":
        return "Summary not available."

    try:
        # Initialize the language model and output parser
        parser = StrOutputParser()
        prompt_template = PromptTemplate(
            template="""
    Based on the provided content, generate a concise and cohesive Executive Summary in one paragraph, strictly limited to 5 lines. 
    Ensure numerical values are accurate and unchanged. Avoid any introductions, explanations, or additional text.

    Content: {content}

    Executive Summary: <Your Response>
    """,
            input_variables=["content"],
        )

        # Initialize the language model instance
        lm_instance = LanguageModel(type="ChatOllama")
        llm = lm_instance.get_llm()

        # Create the summary chain using the prompt and the language model
        summary_chain = prompt_template | llm | parser

        # Invoke the chain with the provided document content
        summary_response = summary_chain.invoke({"content": contents})
        logger.info(f"Short Summary: {summary_response}")
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
