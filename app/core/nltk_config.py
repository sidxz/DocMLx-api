import os
import nltk
from pathlib import Path

# Define the NLTK data directory relative to the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
NLTK_DATA_PATH = PROJECT_ROOT / "nltk_data"
SPACY_DATA_PATH = PROJECT_ROOT / "spacy_data"
def setup_nltk():
    """
    Configures NLTK data path and ensures required resources are available.
    """
    try:
        # Create the NLTK data directory if it doesn't exist
        NLTK_DATA_PATH.mkdir(parents=True, exist_ok=True)
        
        # Add the custom path to NLTK's data search paths
        nltk.data.path.append(str(NLTK_DATA_PATH))

        # Download required NLTK resources if not already downloaded
        required_resources = ['punkt', 'punkt_tab']
        for resource in required_resources:
            if not nltk.download(resource, download_dir=str(NLTK_DATA_PATH)):
                raise RuntimeError(f"Failed to download NLTK resource: {resource}")

        print(f"NLTK setup complete. Data stored at: {NLTK_DATA_PATH}")
    except Exception as e:
        print(f"Error during NLTK setup: {e}")
        raise

# Initialize NLTK setup when the module is imported
setup_nltk()
