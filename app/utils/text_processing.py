from nltk.tokenize import word_tokenize, sent_tokenize
import re
from app.core.nltk_config import setup_nltk  # Ensure NLTK is configured

def count_words_nltk(input_string: str) -> int:
    """
    Counts the number of actual words in a string using NLTK's tokenizer.
    Excludes punctuation, special characters, and numbers.

    Parameters:
        input_string (str): The string to analyze.

    Returns:
        int: Number of actual words in the string.
    """
    if not isinstance(input_string, str):
        raise ValueError("Input must be a string.")
    
    # Tokenize the input string
    tokens = word_tokenize(input_string)
    
    # Filter tokens to include only alphabetic words
    words = [token for token in tokens if token.isalpha()]
    print(words)
    
    return len(words)

def contains_bullet_points(input_text: str) -> bool:
    """
    Checks if the input text contains bullet points or list items.

    Parameters:
        input_text (str): The text to analyze.

    Returns:
        bool: True if bullet points are detected, False otherwise.
    """
    if not isinstance(input_text, str):
        raise ValueError("Input must be a string.")
    
    # Tokenize the text into sentences
    sentences = sent_tokenize(input_text)
    
    # Regex pattern for bullet points or list indicators
    bullet_pattern = re.compile(r"^(\s*[-*•]|\d+[\.)]|\w[\.)])\s+.*")
    
    # Check for matches
    return any(bullet_pattern.match(sentence) for sentence in sentences)

# Example Usage
# if __name__ == "__main__":
#     sample_text_with_bullets = "Here are some points: • First item. 1. Second item. * Third item."
#     sample_text_without_bullets = "This is just regular text with no bullets."

#     print("Word count:", count_words_nltk(sample_text_with_bullets))
#     print("Contains bullets:", contains_bullet_points(sample_text_with_bullets))
#     print("Word count:", count_words_nltk(sample_text_without_bullets))
#     print("Contains bullets:", contains_bullet_points(sample_text_without_bullets))
