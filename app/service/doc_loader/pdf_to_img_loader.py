from typing import List
from pdf2image import convert_from_path
import os
import io
from app.core.logging_config import logger

def pdf_to_png_byte_streams(pdf_path: str, dpi: int = 300) -> List[io.BytesIO]:
    """
    Convert a PDF file into a list of in-memory PNG image byte streams.

    Args:
        pdf_path (str): The file path to the PDF document.
        dpi (int, optional): Resolution in DPI for converting PDF pages. Defaults to 300.

    Returns:
        List[io.BytesIO]: A list of byte streams containing PNG images, one per page.
    """
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found at: {pdf_path}")
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")
    
    images = convert_from_path(pdf_path, dpi=dpi)
    png_streams = []

    for img in images:
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        png_streams.append(img_byte_arr)

    return png_streams