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

    def query_with_image(
        self, prompt: str, image_base64: str, role: str = "user"
    ) -> str:
        """
        Queries the LLM with a prompt and an image.

        Args:
            prompt (str): Text prompt to send.
            image_base64 (str): Base64-encoded image string.
            role (str): Role of the message sender, defaults to "user".

        Returns:
            str: The content of the LLM response.

        Raises:
            NotImplementedError: If image input is not supported by the model type.
            RuntimeError: For any failure during the query execution.
        """
        if self.model_type != "ChatOllama":
            logger.error("Image input requested but unsupported by the current model.")
            raise NotImplementedError(
                "Image input is only supported for ChatOllama models."
            )

        try:
            logger.debug("Sending query with image to the model.")
            response = self.llm.invoke(
                [
                    {
                        "role": role,
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                },
                            },
                        ],
                    }
                ]
            )
            return response.content

        except Exception as query_err:
            logger.exception("An error occurred while querying the model with image.")
            raise RuntimeError(
                "Failed to process image query with the language model."
            ) from query_err
