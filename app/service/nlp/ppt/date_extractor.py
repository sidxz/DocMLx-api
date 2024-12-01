import re
import dateparser
from app.core.logging_config import logger
from app.service.lm.ppt.extractors.date_extractor import extract_dates_from_first_page


def preprocess_text(text):
    """
    Preprocess text to normalize formatting and separate concatenated words,
    months, and numbers for better regex matching.

    Args:
        text (str): The input text to preprocess.

    Returns:
        str: Preprocessed text.
    """
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove unwanted punctuation while retaining commas, periods, and slashes
    text = re.sub(r"[^\w\s,./-]", "", text)

    # Add spaces before full or abbreviated month names if joined with other text
    text = re.sub(
        r"(?<=[a-zA-Z])(?=(January|February|March|April|May|June|July|August|September|October|November|December|"
        r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))",
        r" ",
        text,
        flags=re.IGNORECASE,
    )

    # Add spaces after month names if joined with numbers
    text = re.sub(
        r"(January|February|March|April|May|June|July|August|September|October|November|December|"
        r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(?=\d)",
        r"\1 ",
        text,
        flags=re.IGNORECASE,
    )

    # Remove ordinal suffixes from numbers (e.g., "19th" -> "19")
    text = re.sub(r"(\d)(st|nd|rd|th)", r"\1", text, flags=re.IGNORECASE)

    # Normalize multiple spaces
    return re.sub(r"\s+", " ", text).strip()


def extract_date(file_name: str, first_page_content: str) -> str:
    """
    Extracts a date from the file name or the first page content of a document.
    Uses regex to identify potential date phrases and dateparser for parsing.

    Args:
        file_name (str): The name of the document file.
        first_page_content (str): The text content of the first page of the document.

    Returns:
        str: Extracted date in ISO format (YYYY-MM-DD), or "Unknown" if no valid date is found.
    """
    # Regex pattern for capturing date-like phrases
    date_regex = (
        r"(?<!\d)(\d{1,2}(?:st|nd|rd|th)?\s*(?:January|February|March|April|May|June|July|August|September|October|November|December|"
        r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[,\s]*\d{4}|"
        r"(?:January|February|March|April|May|June|July|August|September|October|November|December|"
        r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[,\s]*\d{1,2}(?:st|nd|rd|th)?[,\s]*\d{4}|"
        r"\d{4}[-/]\d{1,2}[-/]\d{1,2}|"
        r"\d{1,2}[-/]\d{1,2}[-/]\d{4}|"
        r"\d{1,2}[-/]\d{1,2}[-/]\d{2})(?!\d)"
    )

    def extract_date_candidates(text):
        """
        Extracts potential date candidates using regex.

        Args:
            text (str): Input text to search for date candidates.

        Returns:
            list: List of potential date phrases.
        """
        return re.findall(date_regex, text, re.IGNORECASE)

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
                return date.strftime("%Y-%m-%d")
        return None

    # Extract and parse date from file name
    file_name_candidates = extract_date_candidates(file_name)
    date = parse_with_dateparser(file_name_candidates)
    if date:
        # convert date to datetime object
        return dateparser.parse(date)

    # Preprocess and extract date from the first page content
    preprocessed_content = preprocess_text(first_page_content)
    content_candidates = extract_date_candidates(preprocessed_content)
    date = parse_with_dateparser(content_candidates)

    if date:
        return dateparser.parse(date)

    # Try LLM-based date extraction
    extracted_dates = extract_dates_from_first_page(first_page_content, file_name)
    # parse_with_dateparser(date)
    logger.info(f"Date extraction response: {date}")
    date = parse_with_dateparser(extracted_dates)

    # Return extracted date or "Unknown" if no valid date is found
    return dateparser.parse(date) if date else None
