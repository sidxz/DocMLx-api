from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.llm import LanguageModel
from app.core.logging_config import logger


def summary_context_filter(original_content: str, summary_content: str) -> str:

    logger.debug("Applying context filter.")

    parser = StrOutputParser()

    # Define the prompt template for extracting author information
    prompt_template = PromptTemplate(
        template="""
    Compare the provided "Summary" with the "Original Text" to ensure absolute factual accuracy. 
    Verify that every statement in the summary is directly supported by and traceable to the original text. 
    If any part of the summary includes details, interpretations, or data that are not explicitly found in the original text, remove or revise those parts to align exactly with the original text. 
    Retain numerical values and key details as presented in the original text without modification.

    Do not make assumptions, generate new data, or include inferred information. 
    Exclude hallucinations, synthetic data, or any details that cannot be directly matched to the original text. 

    If the summary is already accurate and factual, output it as is without changes. Otherwise, provide the corrected version.

    Important: Output only the corrected "Verified Summary" without any explanations, notes, or additional text.

    "Original Text":
    {original_text}

    "Summary":
    {summary_text}

    Verified Summary: <your response>
    """,
        input_variables=["original_text", "summary_text"],
    )

    # Initialize the language model instance
    lm_instance = LanguageModel(type="ChatOllama")
    llm = lm_instance.get_llm()

    # Create the summary chain using the prompt and the language model
    filter_chain = prompt_template | llm | parser

    # Invoke the chain with the provided document content
    try:
        filter_response = filter_chain.invoke(
            {"original_text": original_content, "summary_text": summary_content}
        )
        clean_response = filter_response.replace("Verified Summary:", "").strip()
        logger.info(f"Original Text: {original_content}")
        logger.info(f"Summary Text: {summary_content}")
        logger.info(f"Filtered Summary: {clean_response}")
        return clean_response
    except Exception as e:
        logger.error(f"An error occurred during filtering context: {e}", exc_info=True)
        return "Unknown"
