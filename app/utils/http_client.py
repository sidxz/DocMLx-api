import os
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables from a .env file (if available)
load_dotenv()


def api_client(
    base_url: str,
    endpoint: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    auth_token: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    A generic API client for making HTTP requests.

    Args:
        endpoint (str): The API endpoint to send the request to.
        method (str): The HTTP method to use (default is "GET").
        headers (Dict[str, str], optional): HTTP headers for the request.
        params (Dict[str, Any], optional): Query parameters for the request.
        data (Dict[str, Any], optional): JSON body data for the request.
        auth_token (str, optional): An authorization token for the request.

    Returns:
        Optional[Dict[str, Any]]: The JSON response from the API, or None if an error occurs.
    """
    if not base_url:
        raise ValueError("API_BASE_URL is not set in the environment variables.")

    url = f"{base_url}{endpoint}"
    default_headers = {"accept": "application/json"}
    
    # Add authorization header if auth_token is provided
    if auth_token:
        default_headers['Authorization'] = f'Bearer {auth_token}'

    # Merge provided headers with default headers
    headers = {**default_headers, **(headers or {})}

    try:
        # Select appropriate request method
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, json=data)
                                       
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None