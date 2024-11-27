import os
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import json

from app.utils.http_client import api_client

# Load environment variables from a .env file (if available)
load_dotenv()

def remove_null_fields(data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove fields that are None or null from the dictionary."""
        return {key: value for key, value in data.items() if value is not None}
    
    
def get_document_by_path(path: str) -> Optional[Dict[str, Any]]:
    """
    Fetches a document's data using its path.

    Args:
        path (str): The path to the document.

    Returns:
        Optional[Dict[str, Any]]: The JSON response from the API, or None if an error occurs.
    """
    base_url = os.getenv("DAIKON_DOC_URL")
    endpoint = "/docu-store/parsed-docs/by-path"
    params = {"Path": path}
    return api_client(base_url=base_url, endpoint=endpoint, params=params)


def add_or_update_document(document_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Adds or updates a document in the Daikon document store.

    Args:
        document_data (Dict[str, Any]): The document data to send.

    Returns:
        Optional[Dict[str, Any]]: The JSON response from the API, or None if an error occurs.
    """


    base_url = os.getenv("DAIKON_DOC_URL")
    endpoint = "/docu-store/parsed-docs"
    filtered_data = remove_null_fields(document_data)  # Remove null fields
    #serialized_data = json.dumps(filtered_data)  # Serialize data to JSON
    #print(f"Payload: {serialized_data}")  # Debug the payload

    # Call the API client
    return api_client(
        base_url=base_url,
        endpoint=endpoint,
        method="PUT",
        data=filtered_data,
    )
