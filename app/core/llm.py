from app.core.logging_config import logger
from typing import Optional


class LanguageModel:
    def __init__(
        self, model_type: str, model_name: str = "gemma3:27b", temperature: float = 0.0
    ):
        """
        Initialize the LanguageModel instance with model type, name, and temperature.
        """
        self.model_type = model_type
        self.model_name = model_name
        self.temperature = temperature
        self.llm = self._initialize_llm()

    def _initialize_llm(self):
        """
        Dynamically initializes the appropriate LLM class based on the model type.

        Returns:
            Initialized language model object.

        Raises:
            ImportError: If the required module is not installed.
            ValueError: If the model type is unsupported.
        """
        try:
            if self.model_type == "ChatOllama":
                from langchain_ollama import ChatOllama

                logger.debug(f"Initializing ChatOllama with model: {self.model_name}")
                return ChatOllama(model=self.model_name, temperature=self.temperature)

            elif self.model_type == "ChatOpenAI":
                from langchain_openai import ChatOpenAI

                # Automatic fallback if llama3 is not supported
                model_to_use = (
                    "gpt-4o" if self.model_name == "llama3" else self.model_name
                )
                logger.debug(f"Initializing ChatOpenAI with model: {model_to_use}")
                return ChatOpenAI(model=model_to_use, temperature=self.temperature)

            else:
                raise ValueError(f"Unsupported model type provided: {self.model_type}")

        except ImportError as import_err:
            module_name = (
                "langchain_ollama"
                if self.model_type == "ChatOllama"
                else "langchain_openai"
            )
            logger.exception(f"Required module not found: {module_name}")
            raise ImportError(
                f"Could not import required module '{module_name}'. Please ensure it is installed."
            ) from import_err

    def get_llm(self):
        """
        Getter for the initialized language model.

        Returns:
            Language model object.
        """
        return self.llm

    # Modified query_with_image
    def query_with_image(self, prompt: str, image_base64: str, role: str = "user") -> str:
        if self.model_type != "ChatOllama":
            raise NotImplementedError("Image input is only supported for ChatOllama.")

        try:
            # Directly use ollama.chat if you're dealing with images
            import ollama
            logger.debug("Sending image+prompt via raw Ollama client.")

            response = ollama.chat(
                model=self.model_name,
                messages=[{
                    'role': role,
                    'content': prompt,
                    'images': [image_base64]
                }]
            )
            return response['message']['content']

        except Exception as query_err:
            logger.exception("Failed to query ChatOllama with image input.")
            raise RuntimeError("Failed to query ChatOllama with image.") from query_err
