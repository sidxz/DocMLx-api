import re
import dateparser
from app.core.logging_config import logger


def preprocess_text(text):
    """
    Preprocess text to add spaces between words, numbers, and punctuation,
    improving date detection.
    """
    # Add spaces around punctuation
    text = re.sub(r"([.,;/()])", r" \1 ", text)
    # Add spaces between letters and numbers
    text = re.sub(r"(?<=[a-zA-Z])(?=\d)|(?<=\d)(?=[a-zA-Z])", " ", text)
    # Add spaces between words and month names
    text = re.sub(
        r"(?<=[a-zA-Z])(?=January|February|March|April|May|June|July|August|September|October|November|December)",
        " ",
        text,
    )
    # Remove ordinal suffixes
    text = re.sub(r"(\d)(st|nd|rd|th)", r"\1", text, flags=re.IGNORECASE)
    return text




def extract_date(file_name: str, first_page_content: str) -> str:
    """
    Extracts a date from the file name or the first page content of a document.
    Uses regex to extract potential date phrases, then parses them with dateparser.

    Args:
        file_name (str): The name of the document file.
        first_page_content (str): The text content of the first page of the document.

    Returns:
        str: Extracted date in ISO format (YYYY-MM-DD), or "Unknown" if no valid date is found.
    """
    # Regex pattern for capturing date-like phrases
    # date_regex = (
    #     r"(?<!\d)(\d{1,2}(?:st|nd|rd|th)?\s*(?:January|February|March|April|May|June|July|August|September|October|November|December|"
    #     r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[,\s]*\d{4}|"
    #     r"(?:January|February|March|April|May|June|July|August|September|October|November|December|"
    #     r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*\d{1,2}(?:st|nd|rd|th)?[,\s]*\d{4}|"
    #     r"\d{4}[-/]\d{2}[-/]\d{2}|"
    #     r"\d{1,2}[-/]\d{1,2}[-/]\d{4}|"
    #     r"\d{4})(?!\d)"
    # )
    
    date_regex = (
    r"(?<!\d)(\d{1,2}(?:st|nd|rd|th)?\s*(?:January|February|March|April|May|June|July|August|September|October|November|December|"
    r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[,\s]*\d{4}|"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December|"
    r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[,\s]*\d{4}|"
    r"\d{4}[-/]\d{2}[-/]\d{2}|"
    r"\d{1,2}[-/]\d{1,2}[-/]\d{4})(?!\d)"
)


    def extract_date_candidates(text):
        """
        Extracts potential date candidates using regex.

        Args:
            text (str): Input text to search for date candidates.

        Returns:
            list: List of potential date phrases.
        """
        matches = re.findall(date_regex, text, re.IGNORECASE)
        logger.debug(f"Extracted date candidates: {matches}")
        return matches

    def parse_with_dateparser(date_candidates):
        """
        Parses a list of date candidates using dateparser.

        Args:
            date_candidates (list): List of potential date phrases.

        Returns:
            str: The first valid date in ISO format, or None if no valid date is found.
        """
        
        for candidate in date_candidates:
            date = dateparser.parse(
                candidate,
                settings={"STRICT_PARSING": False, "PREFER_DAY_OF_MONTH": "first"},
            )
            if date:
                return date.strftime("%Y-%m-%d")  # Return the first valid date
        return None

    # Extract and parse date from file name
    file_name_candidates = extract_date_candidates(file_name)
    # date = parse_with_dateparser(file_name_candidates)
    # if date:
    #     logger.debug(f"Date extracted from file name: {date}")
    #     return date

    # Extract and parse date from first page content
    content_candidates = extract_date_candidates(preprocess_text(first_page_content))
    date = parse_with_dateparser(content_candidates)
    if date:
        logger.debug(f"Date extracted from first page content: {date}")
        return date

    # Return "Unknown" if no valid date is found
    logger.warning(f"No valid date found for file: {file_name}")
    return "Unknown"
