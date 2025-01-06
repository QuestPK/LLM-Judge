import json
import requests
from pprint import pprint

from .constants import (
    LOCAL_HOST_URL,
    MODEL_NAME,
)
from .prompts import (
    SYSTEM_PROMPT,
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

def get_response_from_llm(baseline: str, current: str, summary_accepted: bool) -> str:
    """
    Get the score from the LLM.

    Args:
        baseline (str): The baseline string to evaluate against.
        current (str): The current string to score against the baseline.
        summary_accepted (bool): Whether the summary is accepted or not (not used).

    Returns:
        str: The response/score from the LLM, containing the score as a string (e.g. '3').

    Raises:
        Exception: If the endpoint returns an error or response processing fails.
    """
    user_message_str = f"baseline: {baseline}\ncurrent: {current}"

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": user_message_str
        }
    ]

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
