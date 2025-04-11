from typing import List
from langchain_core.documents import Document
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.llm import LanguageModel
from app.core.logging_config import logger
from app.service.lm.generic.correctors.context_filter import summary_context_filter
import pandas as pd
from tabulate import tabulate


def generate_exec_summary(content: List[str], topic: str) -> str:
    """
    Summarizes the content

    Args:
        content: The list of text content of the slides.

    Returns:
        str: The summarized content of the slide or an "Unknown" message if an error occurs.
    """
    logger.debug("Starting executive slide summarization.")

    contents = " ".join(content)  # Join the list of strings into a single string
    if contents.strip() == "":
        return "Summary not available."

    try:
        # Initialize the language model and output parser
        parser = StrOutputParser()
        prompt_template = PromptTemplate(
            template="""
            As a TB drug discovery portfolio manager, I will create a high-level summary of the research on "{topic}". 
            The summary will synthesize key information from the provided page summaries into 15-20 sentences, tailored specifically for portfolio managers.

            The summary will include:

            - **Research Objectives**: Focus on alignment with overall project aims.
            - **TB Protein/Target**: Emphasize its strategic importance.
            - **Compounds**: Highlight potential impact and development stage.
            - **Project Stages and Progress**: Detail timelines, milestones, and completion percentages.
            - **Key Findings**: Summarize for strategic relevance.
            - **Challenges**: Identify potential risks and mitigation strategies.
            - **Future Directions**: Focus on project timelines, deliverables, and resource needs.

            Begin directly with the synthesized summary, emphasizing overall status, progress, and strategic elements.
            Do NOT include any System generated introductory statements or follow-up questions.

            Page Summaries: {page_summaries}

            **Executive Summary**:
            """,
            input_variables=["page_summaries", "topic"],
        )

        # Initialize the language model instance
        lm_instance = LanguageModel(model_type="ChatOllama")
        llm = lm_instance.get_llm()

        # Create the summary chain using the prompt and the language model
        summary_chain = prompt_template | llm | parser

        # Invoke the chain with the provided document content
        summary_response = summary_chain.invoke(
            {"topic": topic, "page_summaries": contents}
        )
        logger.info(f"Exec Summary: {summary_response}")
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
