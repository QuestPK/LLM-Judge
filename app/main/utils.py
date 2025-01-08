import json
import requests
from pprint import pprint

from .constants import (
    LOCAL_HOST_URL,
    MODEL_NAME,
)
from .prompts import (
    SYSTEM_PROMPT,
    SUMMARY_CHECK_PROMPT
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

        print(f"\nSending request to {LOCAL_HOST_URL} with data: {data.keys()} and model: {MODEL_NAME}")

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
    
def check_if_summary(baseline: str, current: str):
    """
    Check if the summary is present in the current string.

    Args:
        baseline (str): The baseline string.
        current (str): The current string to check for the summary.

    Returns:
        bool: True if the current is a summary of the baseline or viceversa.
    """
    user_message_str = f"baseline: {baseline}\ncurrent: {current}"

    messages = [
        {
            "role": "system",
            "content": SUMMARY_CHECK_PROMPT
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
    
    try:
        summary_data = json.loads(response.get("message", {}).get("content", ""))
    except json.JSONDecodeError as e:
        print("Issue decoding JSON response:", e)
        summary_data = response.get("message", {}).get("content", "")
 
    print("\nIs summary:")
    pprint(summary_data)

    is_summary = summary_data.get("is_summary", False)

    return is_summary

def get_score_from_llm(question: str, baseline: str, current: str) -> dict:
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

    user_message_str = f"question: {question}\nbaseline: {baseline}\ncurrent: {current}"

    system_prompt = SYSTEM_PROMPT

    messages = [
        {
            "role": "system",
            "content": system_prompt
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
    except json.JSONDecodeError as e:
        print("Issue decoding JSON response:", e)
        raise Exception("Failed to decode JSON response" + str(e))
 
    total_rating = result.get("Total rating", 0)
    reason = result.get("Reason", "")

    print("\n\nTotal rating: ", total_rating)
    print("Reason: ", reason)

    return {
        "score": total_rating,
        "reason": reason
    }

def get_score_data(question: str, baseline: str, current: str, summary_accepted: bool) -> dict:
    """ 
    Args:
        baseline (str): The baseline string to evaluate against.
        current (str): The current string to score against the baseline.
        summary_accepted (bool): Whether the summary is accepted or not (not used).

    Returns:
        str: The response/score from the LLM, containing the score as a string (e.g. '3').

    """
    score_data = get_score_from_llm(question, baseline, current)

    if not summary_accepted:
        is_summary = check_if_summary(baseline, current)

        if is_summary:
            return { 
                "score": 0,
                "reason": "We found summary in the string. Score updated."
            }

    return {
        "score": score_data.get("score", 0),
        "reason": score_data.get("reason", "")
    }
