from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from app.core.llm import LanguageModel
from app.core.logging_config import logger
from app.schema.parser_objects.target import Target
from app.constants.target_names import target_names


def extract_target_from_first_page(first_page_content: str, file_name: str) -> str:
    """
    Extracts the name of the target from the first page content of a document.

    Args:
        first_page_content (str): The text content of the first page of the document.
        file_name (str): The name of the document file.

    Returns:
        str: The extracted target a string or 'Unknown' if not found.
    """
    logger.debug("Starting target extraction from the first page and title of the document.")

    parser = JsonOutputParser(pydantic_object=Target)

    # Define the prompt template for extracting author information
    prompt_template = PromptTemplate(
        template="""Parse the name of a Tuberculosis Drug Target, which is a protein of Mycobacterium tuberculosis strain H37Rv, from the information provided. Examples of known targets include Rho, PknB, and PptT.

    **Rules for Parsing:**
    1. Use the 'File Name' as the primary source for finding the target name.
    2. Use the 'Document' as a secondary hint if the target name cannot be found in the file name.
    3. If a target name cannot be found in either the 'Document' or 'File Name', return "Unknown."
    4. Only return names explicitly mentioned in the provided inputs. Do not infer or guess names.
    5. The target name should be a protein of Mycobacterium tuberculosis strain H37Rv. This would never be a english word or a common name.
    - Do not include explanations, introductory statements, or any additional text.

    **Input:**
    File Name: {file_name}
    Document: {document}
    
    **Output:**
    Format Instructions: {format_instructions}""",
        input_variables=["document", "file_name"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    # Initialize the language model instance

    lm_instance = LanguageModel(type="ChatOllama")
    llm = lm_instance.get_llm()

    # Create the target extraction chain using the prompt and the language model
    target_chain = prompt_template | llm | parser

    # Invoke the chain with the provided document content
    try:
        target_response = target_chain.invoke(
            {"document": first_page_content, "file_name": file_name}
        )
        logger.info(f"Target extraction response: {target_response}")
        # Validate the extracted target against known target names
        extracted_target = target_response.get("target", "").strip()
        if extracted_target.lower() in target_names:
            return extracted_target
        else:
            logger.warning(f"Extracted target '{extracted_target}' is not in the known target names.")
            return "Unknown"
    except Exception as e:
        logger.error(f"An error occurred during target extraction: {e}")
        return "Unknown"




def extract_target_from_summary(summary: str, topic: str) -> str:
    """
    Extracts the name of the target from the summary.

    Args:
        summary (str): The summary of the document.
        topic (str): The topic of the document.

    Returns:
        str: The extracted target as a string or 'Unknown' if not found.
    """
    logger.debug("Starting target extraction from summary.")

    parser = JsonOutputParser(pydantic_object=Target)

    # Define the prompt template for extracting author information
    prompt_template = PromptTemplate(
        template="""Parse the name of a Tuberculosis Drug Target, which is a protein of Mycobacterium tuberculosis strain H37Rv, from the information provided. Examples of known targets include Rho, PknB, and PptT.

    **Rules for Parsing:**
    1. Use the 'Summary' as the source for finding the target name.
    2. Use the 'Topic' as a hint.
    3. If a target name cannot be found in either the 'Summary' or 'Topic', return "Unknown."
    4. Only return names explicitly mentioned in the provided inputs. Do not infer or guess names.
    5. The target name should be a protein of Mycobacterium tuberculosis strain H37Rv. This would never be a english word or a common name.
    - Do not include explanations, introductory statements, or any additional text.

    **Input:**
    Topic: {topic}
    Summary: {summary}
    
    **Output:**
    Format Instructions: {format_instructions}""",
        input_variables=["topic", "summary"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    # Initialize the language model instance

    lm_instance = LanguageModel(type="ChatOllama")
    llm = lm_instance.get_llm()

    # Create the target extraction chain using the prompt and the language model
    target_chain = prompt_template | llm | parser

    # Invoke the chain with the provided document content
    try:
        target_response = target_chain.invoke(
            {"topic": topic, "summary": summary}
        )
        logger.info(f"Target extraction response: {target_response}")
        # Validate the extracted target against known target names
        extracted_target = target_response.get("target", "").strip()
        if extracted_target.lower() in target_names:
            return extracted_target
        else:
            logger.warning(f"Extracted target '{extracted_target}' is not in the known target names.")
            return "Unknown"
    except Exception as e:
        logger.error(f"An error occurred during target extraction: {e}")
        return "Unknown"