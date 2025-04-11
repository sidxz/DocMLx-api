from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from app.core.llm import LanguageModel
from app.core.logging_config import logger
from app.schema.parser_objects.author import AuthorNames


def extract_author_from_first_page(first_page_content: str, file_name: str) -> str:
    """
    Extracts the name of the author(s) from the first page content of a document.

    Args:
        first_page_content (str): The text content of the first page of the document.
        file_name (str): The name of the document file.

    Returns:
        str: The extracted author(s) name(s) as a string or 'Unknown' if not found.
    """
    logger.debug("Starting author extraction from the first page of the document.")

    parser = JsonOutputParser(pydantic_object=AuthorNames)

    # Define the prompt template for extracting author information
    prompt_template = PromptTemplate(
        template="""I will extract the name of the author or authors from the provided 'Document':
    I can take a hint from the 'File Name', that might contain a part of the author's name.
    
    If there are multiple authors, I will list them all. Multiple authors might be separated by a comma or 'and'.
    If I cannot find the author, I will print Unknown
    
    Important: I will provide only the JSON output without any introductory statements, explanations, or additional text.
    
    Document: {document}
    File Name: {file_name}
    Author(s):
    Format Instructions: {format_instructions}
    """,
        input_variables=["document", "file_name"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    # Initialize the language model instance

    lm_instance = LanguageModel(model_type="ChatOllama")
    llm = lm_instance.get_llm()

    # Create the author extraction chain using the prompt and the language model
    author_chain = prompt_template | llm | parser

    # Invoke the chain with the provided document content
    try:
        author_response = author_chain.invoke(
            {"document": first_page_content, "file_name": file_name}
        )
        logger.info(f"Author extraction response: {author_response}")
        return author_response["names"]
    except Exception as e:
        logger.error(
            f"An error occurred during author extraction: {e}"
        )
        return ["Unknown"]
