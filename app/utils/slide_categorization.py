from io import BytesIO
from PIL import Image
from langchain.prompts import PromptTemplate

from app.core.llm import LanguageModel
from app.core.logging_config import logger
from app.utils.img_processing import preprocess_img_for_llm, image_to_base64

"""
/*
 * Function: is_backup_slide
 * --------------------------
 * Determines whether a slide qualifies as a "backup slide" based on content and image.
 *
 * Parameters:
 *   text_content (str)     - Extracted OCR/parsed text from the slide.
 *   img_content (BytesIO)  - Raw binary image content of the slide.
 *
 * Returns:
 *   str - "true", "false", or error indicator string.
 */
"""


def is_backup_slide(text_content: str, img_content: BytesIO) -> str:
    logger.debug("Checking if slide is a backup slide.")

    try:
        # Step 1: Open and preprocess the image
        image = Image.open(img_content)
        preprocessed_image = preprocess_img_for_llm(
            image, enhance_contrast=True, sharpen=True, resize=True, denoise=True
        )
        img_base64 = image_to_base64(preprocessed_image)

    except Exception as e:
        logger.error("Image preprocessing failed.", exc_info=True)
        return "Unknown"

    try:
        # Step 2: Define prompt template
        backup_prompt = PromptTemplate(
            input_variables=["parsed_text"],
            template="""
You are given a single slide from a presentation. The slide may contain text and images.

Definition:
A backup slide is a placeholder slide typically shown at the end of a presentation. 
It usually contains only the word “Backup,” “Backup Slide,” "Back-up", “Additional Slides,” or a similar phrase. 
These slides are often completely blank or contain no meaningful scientific or technical content — just the label indicating that backup material follows.

Task:
Based solely on the content of this single slide, decide if it matches the definition of a backup slide above.

Important:
Do not classify the slide as a backup if the word "backup" appears in another context (e.g., "data backup", "backup strategy", "backup experiment") and the slide contains other meaningful content.

Output:
Return only one word:

true — if this is a backup slide  
false — if this is not a backup slide

Rules:
Do not explain your reasoning.  
Do not return anything except true or false.  
If there is no input, say false

Text:
{parsed_text}

<Your Response>
""",
        )

        formatted_prompt = backup_prompt.format(parsed_text=text_content)

        # Step 3: Initialize model and send query
        lm = LanguageModel(model_type="ChatOllama")
        response = lm.query_with_image(prompt=formatted_prompt, image_base64=img_base64)

        logger.info(f"Backup slide detected? {response.strip()}")
        return response.strip()

    except ValueError as ve:
        logger.error("Validation error during backup detection.", exc_info=True)
        return "Invalid slide content."
    except ConnectionError as ce:
        logger.error("Connection error while querying the model.", exc_info=True)
        return "Connection error. Try again later."
    except Exception as e:
        logger.exception("Unexpected error during backup slide detection.")
        return "Unknown"
