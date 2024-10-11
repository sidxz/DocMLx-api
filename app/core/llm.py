from app.core.logging_config import logger
class LanguageModel:
    def __init__(self, type: str, model: str = "llama3", temperature: float = 0.0):
        """
        Initializes a language model based on the specified type and model parameters.

        Args:
            type (str): The type of language model, e.g., "ChatOllama" or "ChatOpenAI".
            model (str): The model name to use. Default is "llama3".
            temperature (float): The temperature setting for the model. Default is 0.0.

        Raises:
            ValueError: If an unsupported model type is provided.
            ImportError: If the required library for the model type is not installed.
        """
        self.llm = self._initialize_llm(type, model, temperature)

    def _initialize_llm(self, type: str, model: str, temperature: float):
        """
        Private method to initialize the language model based on the type.

        Args:
            type (str): The type of language model, e.g., "ChatOllama" or "ChatOpenAI".
            model (str): The model name to use.
            temperature (float): The temperature setting for the model.

        Returns:
            An instance of the language model.

        Raises:
            ValueError: If an unsupported model type is provided.
            ImportError: If the required library for the model type is not installed.
        """
        if type == "ChatOllama":
            try:
                from langchain_ollama import ChatOllama
                logger.debug(f"Language model initialized: {type} - {model}")
                return ChatOllama(model=model, temperature=temperature)
            except ImportError as e:
                raise ImportError(
                    "Could not import ChatOllama. Make sure 'langchain_ollama' is installed."
                ) from e

        elif type == "ChatOpenAI":
            try:
                from langchain_openai import ChatOpenAI

                # Adjust model name if "llama3" is used
                if model == "llama3":
                    model = "gpt-4o"
                logger.debug(f"Language model initialized: {type} - {model}")
                return ChatOpenAI(model=model, temperature=temperature)
            except ImportError as e:
                raise ImportError(
                    "Could not import ChatOpenAI. Make sure 'langchain_openai' is installed."
                ) from e

        else:
            raise ValueError(f"Unsupported model type: {type}")
        

    def get_llm(self):
        """
        Returns the instantiated language model object.

        Returns:
            The language model object.
        """
        return self.llm
