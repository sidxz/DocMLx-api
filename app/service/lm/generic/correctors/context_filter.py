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
        Given the following "Original Text" and its "Summary", please review the summary and compare it with the original text. 
        Ensure that every piece of information presented in the summary is supported and directly traceable back to the original text. 
        If any information in the summary is not explicitly found in the original text, remove it to align precisely with the content and details of the original text.
        Include exceptions or negative results, and retain numerical values as is.
        
        If the Summary is accurate and does not require any changes, just output the Verified Summary to be the same as summary.
        
        Important: Output directly the value of Verified Summary (<your response>) and do NOT include any introductory statements, explanations, notes etc.
        
        "Original Text":
        {original_text}

        "Summary":
        {summary_text}

        <your response>
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
