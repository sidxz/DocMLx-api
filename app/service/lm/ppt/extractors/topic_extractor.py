from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from app.core.llm import LanguageModel
from app.core.logging_config import logger
from app.schema.parser_objects.author import AuthorNames
from app.schema.parser_objects.topic import Topic


def extract_topic_from_first_page(first_page_content: str) -> str:
    """
    Extracts the topic from the first page content of a document.

    Args:
        first_page_content (str): The text content of the first page of the document.

    Returns:
        str: The extracted topic as a string or 'Unknown' if not found.
    """
    logger.debug("Starting topic extraction from the first page of the document.")

    parser = JsonOutputParser(pydantic_object=Topic)

    # Define the prompt template for extracting author information
    prompt_template = PromptTemplate(
        template="""I will extract the topic from the provided page of the 'Document':
    The 'Document' is taken from the first page of a presentation, and the topic will be in a sentence or a few words.
    
    I will return the topic as is, without any additional processing or modifications.
    If I cannot find the topic, I will print Unknown
    
    Important: I will provide only the JSON output without any introductory statements, explanations, or additional text.
    
    Document: {document}
    Topic:
    Format Instructions: {format_instructions}
    """,
        input_variables=["document"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    # Initialize the language model instance

    lm_instance = LanguageModel(type="ChatOllama")
    llm = lm_instance.get_llm()

    # Create the topic extraction chain using the prompt and the language model
    topic_chain = prompt_template | llm | parser

    # Invoke the chain with the provided document content
    try:
        topic_response = topic_chain.invoke({"document": first_page_content})
        logger.info(f"Topic extraction response: {topic_response}")
        return topic_response["topic"]
    except Exception as e:
        logger.error(f"An error occurred during topic extraction: {e}")
        return "Unknown"
