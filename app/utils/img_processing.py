from PIL import Image, ImageEnhance, ImageFilter
from app.core.logging_config import logger
import io
import base64
from PIL import Image, ImageEnhance, ImageFilter
import logging

# Configure logger at module level (can be moved to a config file or main application entry)
logger = logging.getLogger(__name__)


def preprocess_img_for_llm(
    image: Image.Image,
    enhance_contrast: bool = True,
    sharpen: bool = True,
    resize: bool = True,
    denoise: bool = True,
) -> Image.Image:
    """
    /*
     * Preprocesses slide images for Vision-Language LLM input (not OCR-specific).
     * This process maintains layout, color, and clarity for optimal multimodal understanding.
     *
     * Parameters:
     * image (PIL.Image.Image): The input image to preprocess.
     * enhance_contrast (bool): Apply contrast enhancement. Default is True.
     * sharpen (bool): Apply image sharpening. Default is True.
     * resize (bool): Resize image if below target width. Default is True.
     * denoise (bool): Apply light denoising (Gaussian blur). Default is True.
     *
     * Returns:
     * PIL.Image.Image: The preprocessed image.
     *
     * Raises:
     * ValueError: If the input is not a valid PIL Image.
     */
    """

    logger.debug("Starting image preprocessing for LLM.")

    if not isinstance(image, Image.Image):
        raise ValueError("Expected a PIL.Image.Image object.")

    try:
        # Ensure the image is in RGB mode for consistent processing
        if image.mode != "RGB":
            image = image.convert("RGB")
            logger.debug("Image converted to RGB mode.")

        # Resize if necessary to ensure sufficient resolution for LLM input
        target_width = 1600
        max_height = 2000

        if resize and image.width < target_width:
            scale_ratio = target_width / image.width
            new_height = min(int(image.height * scale_ratio), max_height)
            image = image.resize((target_width, new_height), Image.LANCZOS)
            logger.debug(f"Image resized to {target_width}x{new_height}.")

        # Slight contrast enhancement to improve clarity
        if enhance_contrast:
            contrast_enhancer = ImageEnhance.Contrast(image)
            image = contrast_enhancer.enhance(1.4)
            logger.debug("Contrast enhanced by factor 1.4.")

        # Apply gentle denoising to remove compression artifacts
        if denoise:
            image = image.filter(ImageFilter.GaussianBlur(radius=0.3))
            logger.debug("Applied Gaussian blur for denoising (radius=0.3).")

        # Slight sharpening for better edge clarity, especially helpful for small text
        if sharpen:
            image = image.filter(ImageFilter.SHARPEN)
            logger.debug("Applied image sharpening.")

        return image

    except Exception as e:
        logger.error(f"Error during image preprocessing: {e}")
        raise RuntimeError("Failed to preprocess image for LLM input.") from e


def image_to_base64(image: Image.Image, format: str = "PNG") -> str:
    """
    /*
     * Converts a PIL Image object to a Base64-encoded string.
     *
     * Parameters:
     * image (PIL.Image.Image): The input image to encode.
     * format (str): The image format (default is 'PNG').
     *
     * Returns:
     * str: A Base64-encoded string representation of the image.
     *
     * Raises:
     * ValueError: If the image is not a valid PIL Image object.
     * IOError: If an error occurs during image saving or encoding.
     */
    """

    if not isinstance(image, Image.Image):
        raise ValueError("Invalid image: expected a PIL Image object.")

    try:
        # Use BytesIO as an in-memory buffer to store image binary data
        with io.BytesIO() as buffer:
            # Save the image into the buffer using the specified format
            image.save(buffer, format=format)
            # Retrieve byte data from the buffer
            byte_data = buffer.getvalue()

        # Encode the byte data to Base64 and return as UTF-8 string
        return base64.b64encode(byte_data).decode("utf-8")

    except Exception as e:
        raise IOError(f"Failed to convert image to Base64: {str(e)}") from e
