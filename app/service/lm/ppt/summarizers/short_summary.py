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
    content: List[str],
    BATCH_1_SIZE: int = 2,
    BATCH_N_SIZE: int = 2,
    MIDDLE_BATCH_SIZE: int = 10,
) -> str:
    logger.debug("Starting short summarization.")

    # Validate input
    if not content or all(not slide.strip() for slide in content):
        logger.warning("Empty or invalid content provided.")
        return "Summary not available."

    try:
        # --- Prompt templates ---
        batch_prompt_template = PromptTemplate(
            input_variables=["content"],
            template="""
You are given a collection of slide-level summaries from a tuberculosis drug discovery research presentation.

Task:
- From the provided content, **select at most five complete sentences** that best represent the key takeaways.
- You are NOT allowed to rephrase, summarize, or generate new interpretations.
- **Only pick sentences that are already present verbatim in the provided content.**
- If the content has fewer than five sentences, include as many as possible without inventing or completing any.

Requirements:
- **Do not mention that this is a TB drug discovery program** — the audience already knows this.
- The output must be a single paragraph (no more than 5 lines).
- Do not use bullet points, lists, headings, or introductory phrases.
- Do not add context, interpretations, or conclusions beyond the provided text.
- Maintain original phrasing, do not alter abbreviations, terminology, or emphasis used in the slides.

Important:
- Your output must be only the final paragraph with the selected sentences.
- Do not include explanations, instructions, or extra formatting.

Content:
{content}

Summary:
            """,
        )

        final_prompt_template = PromptTemplate(
            input_variables=["content"],
            template="""
You are given summarized slide content from a tuberculosis drug discovery presentation, structured as:
1. Batch 1: Presentation objectives (must be prioritized)
2. Middle: Summarized body slides (supporting details)
3. Batch N: Conclusion slides 

Task:
- From the provided content, select at most ten complete sentences that best represent the key takeaways.
- You are NOT allowed to rephrase, summarize, or generate new interpretations.
- Only select sentences that are already present verbatim in the provided content.
- Try prioritizing sentences from Batch 1 (objectives) if they are informative.
- After covering objectives, select other important sentences from the middle and conclusion content.
- If fewer than ten good sentences are available, select as many as possible without inventing or completing any.

Requirements:
- Do not create bullet points, lists, or headings.
- Do not add background information, explanations, or conclusions.
- Do not modify abbreviations, terminology, or phrasing used in the slides.
- Avoid introductory phrases like "In summary".

Important:
- Output should be a single coherent paragraph containing the selected sentences.
- No extra formatting, no titles, no instructions.

Content:
{content}

Summary:
            """,
        )

        refinement_prompt_template = PromptTemplate(
            input_variables=["content"],
            template="""
You are given a paragraph containing selected sentences from a tuberculosis drug discovery presentation.

Task:
- Rewrite to improve clarity, coherence, and logical flow.
- Reorder sentences only if needed. Prefer to keep the original order unless it disrupts flow.
- Correct minor grammar inconsistencies.
- Do NOT add new information or rephrase technical terms.

Requirements:
- Preserve factual content.
- Keep it as a single paragraph.
- No bullet points, no extra context, no summaries.

Content:
{content}

Refined Summary:
            """,
        )

        # --- Chains ---
        parser = StrOutputParser()
        llm = LanguageModel(model_type="ChatOllama").get_llm()
        batch_summary_chain = batch_prompt_template | llm | parser
        final_summary_chain = final_prompt_template | llm | parser
        refinement_chain = refinement_prompt_template | llm | parser

        total_slides = len(content)
        BATCH_1_SIZE = min(BATCH_1_SIZE, total_slides)
        BATCH_N_SIZE = min(BATCH_N_SIZE, max(0, total_slides - BATCH_1_SIZE))

        batch_1 = content[:BATCH_1_SIZE]
        batch_n = content[-BATCH_N_SIZE:] if BATCH_N_SIZE > 0 else []
        middle_content = (
            content[BATCH_1_SIZE : total_slides - BATCH_N_SIZE]
            if total_slides > (BATCH_1_SIZE + BATCH_N_SIZE)
            else []
        )

        # --- Process BATCH 1 ---
        joined_batch_1 = "\n".join(slide.strip() for slide in batch_1 if slide.strip())
        logger.info(f"--- BATCH 1 CONTENT ---\n{joined_batch_1}")
        batch_1_summary = batch_summary_chain.invoke({"content": joined_batch_1})
        logger.info(f"--- BATCH 1 SUMMARY ---\n{batch_1_summary}")

        # --- Process Middle Batches ---
        middle_summaries = []
        for idx in range(0, len(middle_content), MIDDLE_BATCH_SIZE):
            batch = middle_content[idx : idx + MIDDLE_BATCH_SIZE]
            joined_batch = "\n".join(slide.strip() for slide in batch if slide.strip())

            logger.info(
                f"--- MIDDLE BATCH {idx // MIDDLE_BATCH_SIZE + 1} CONTENT ---\n{joined_batch}"
            )
            batch_summary = batch_summary_chain.invoke({"content": joined_batch})
            logger.info(
                f"--- MIDDLE BATCH {idx // MIDDLE_BATCH_SIZE + 1} SUMMARY ---\n{batch_summary}"
            )

            middle_summaries.append(batch_summary)

        # --- Process Batch N ---
        if batch_n:
            joined_batch_n = "\n".join(
                slide.strip() for slide in batch_n if slide.strip()
            )
            logger.info(f"--- BATCH N CONTENT ---\n{joined_batch_n}")
            batch_n_summary = batch_summary_chain.invoke({"content": joined_batch_n})
            logger.info(f"--- BATCH N SUMMARY ---\n{batch_n_summary}")
        else:
            batch_n_summary = ""

        # --- Combine for Final Summary ---
        combined_summary_input = (
            batch_1_summary
            + "\n"
            + "\n".join(middle_summaries)
            + "\n"
            + batch_n_summary
        )

        logger.info("--- FINAL SUMMARY INPUT ---\n" + combined_summary_input)

        final_summary = final_summary_chain.invoke({"content": combined_summary_input})
        logger.info("--- FINAL SUMMARY ---\n" + final_summary)

        refined_summary = refinement_chain.invoke({"content": final_summary})
        logger.info("--- REFINED FINAL SUMMARY ---\n" + refined_summary)

        logger.debug("Short summarization completed successfully.")
        return refined_summary

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
    