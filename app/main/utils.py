import json
import requests
from pprint import pprint

from .constants import (
    LOCAL_HOST_URL,
    MODEL_NAME,
    SYSTEM_PROMPT
)

def retrieve_response_from_endpoint(data: dict) -> dict:
    """
    Sends a POST request to a local endpoint with the provided data.

    Args:
        data (dict): The data to send in the POST request.

    Returns:
        dict: The JSON response from the server.

    Raises:
        RuntimeError: If there is an issue with the request or the response is not JSON.
    """
    try:
        headers = {'Content-Type': 'application/json'}

        print(f"Sending request to {LOCAL_HOST_URL} with data: {data.keys()} and model: {MODEL_NAME}")

        response = requests.post(LOCAL_HOST_URL, json=data, headers=headers)
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
        return response.json()      # Convert response to JSON
    
    except requests.exceptions.RequestException as e:
        # Handle specific request-related exceptions
        raise RuntimeError(f"Request failed: {e}") from e
    
    except ValueError as e:
        # Handle JSON decoding errors
        raise RuntimeError(f"Invalid JSON in response: {e}") from e
    
    except Exception as e:
        # Handle other exceptions
        raise RuntimeError(f"An error occurred: {e}") from e

def get_response_from_llm(messages: list) -> str:
    """
    Formats messages and retrieves a response from the LLM endpoint.

    Args:
        messages (list): List of message dictionaries for the LLM.

    Returns:
        str: The response from the LLM.

    Raises:
        Exception: If the endpoint returns an error or response processing fails.
    """
    system_message = {
        "role": "system",
        "content": SYSTEM_PROMPT
    }

    # Ensure the system message is added at the beginning of the messages list
    messages.insert(0, system_message)

    data = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False
    }

    try:
        response = retrieve_response_from_endpoint(data)
    except Exception as e:
        print(f"Error in get_response_from_llm: {e}")
        # Add context to the exception
        raise Exception(f"Failed to get response from LLM: {e}") from e

    print("\nResults:")
    pprint(response)
    
    try:
        result = json.loads(response.get("message", {}).get("content", ""))
    except json.JSONDECODEError as e:
        print("Issue decoding JSON response:", e)
        result = response.get("message", {}).get("content", "")
 
    result = result.get("Total rating", 0)
    
    return result
