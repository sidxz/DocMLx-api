from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from app.core.llm import LanguageModel
from app.core.logging_config import logger
from app.schema.parser_objects.extracted_dates import ExtractedDates



def extract_dates_from_first_page(first_page_content: str, file_name: str) -> str:
    """
    Extracts the date(s) from the first page content of a document.

    Args:
        first_page_content (str): The text content of the first page of the document.
        file_name (str): The name of the document file.

    Returns:
        str: The extracted date(s) as a string in ISO format or 'Unknown' if not found.
    """
    logger.debug("Starting date extraction from the first page of the document.")

    parser = JsonOutputParser(pydantic_object=ExtractedDates)

    # Define the prompt template for extracting date information
    prompt_template = PromptTemplate(
        template="""I will extract the date(s) from the provided 'Document':
    I can take a hint from the 'File Name', which might contain a date.
    
    If there are multiple dates, I will list them all in ISO format (YYYY-MM-DD).
    If I cannot find any date, I will print Unknown.
    
    Important: I will provide only the JSON output without any introductory statements, explanations, or additional text.
    
    Document: {document}
    File Name: {file_name}
    Date(s):
    Format Instructions: {format_instructions}
    """,
        input_variables=["document", "file_name"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    # Initialize the language model instance
    lm_instance = LanguageModel(type="ChatOllama")
    llm = lm_instance.get_llm()

    # Create the date extraction chain using the prompt and the language model
    date_chain = prompt_template | llm | parser

    # Invoke the chain with the provided document content
    try:
        date_response = date_chain.invoke(
            {"document": first_page_content, "file_name": file_name}
        )
        logger.info(f"Date extraction response: {date_response}")
        return date_response["dates"]
    except Exception as e:
        logger.error(f"An error occurred during date extraction: {e}")
        return ["Unknown"]
