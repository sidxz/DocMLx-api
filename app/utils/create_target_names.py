import os
from app.core.logging_config import logger
from dotenv import load_dotenv
from app.utils.http_client import api_client

load_dotenv()

DAIKON_GENE_URL = os.getenv("DAIKON_GENE_URL")
DAIKON_TARGET_URL = os.getenv("DAIKON_TARGET_URL")


def fetch_and_process_names(base_url, endpoint="/", headers=None):
    """
    Fetch data from the given API URL and extract lowercase names.

    Args:
        base_url (str): The base URL of the API.
        endpoint (str): The API endpoint to fetch data.
        headers (dict): The headers to include in the API request.

    Returns:
        list: A list of lowercase names.
    """
    headers = headers or {"accept": "text/plain; x-api-version=2.0"}

    try:
        logger.info(f"Fetching names from {base_url}{endpoint}...")
        response = api_client(base_url, endpoint, headers=headers)

        if not response:
            logger.warning(f"API at {base_url}{endpoint} returned no data.")
            return []

        # Extract and lowercase names, ensuring name is valid
        names = [
            item["name"].strip().lower()
            for item in response
            if isinstance(item.get("name"), str) and item["name"].strip()
        ]
        logger.info(f"Successfully processed {len(names)} names from {base_url}.")
        return names

    except Exception as e:
        logger.error(f"An error occurred while fetching names from {base_url}: {e}")
        return []


def export_names_to_file(names, filename="app/constants/target_names.py"):
    """
    Export the list of names to a Python file.

    Args:
        names (list): List of names to export.
        filename (str): Name of the Python file to create.
    """
    if not names:
        logger.warning("No names to export.")
        return

    try:
        with open(filename, "w") as file:
            file.write("# This file is auto-generated. Do not edit manually.\n\n")
            file.write(f"target_names = {names}\n")
        logger.info(f"Names have been successfully exported to {filename}.")
    except IOError as e:
        logger.error(f"Failed to export names to {filename}: {e}")


def main():
    """
    Main execution function to fetch and export combined names.
    """
    logger.info("Starting name processing...")

    # Fetch names from gene and target APIs
    gene_names = fetch_and_process_names(DAIKON_GENE_URL, endpoint="/gene")
    target_names = fetch_and_process_names(DAIKON_TARGET_URL, endpoint="/target?WithMeta=false")

    # Combine and deduplicate the names
    combined_names = sorted(set(gene_names + target_names))
    logger.info(f"Total combined and deduplicated names: {len(combined_names)}")

    # Export to file
    export_names_to_file(combined_names)


if __name__ == "__main__":
    main()
