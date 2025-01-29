from datetime import datetime

from flask import request
import requests

def get_current_month_year() -> str:
    """
    Returns the current month and year as a string in 'Month_Year' format.
    """
    return datetime.now().strftime("%B_%Y")  # Example: 'January_2025'

def get_current_datetime() -> str:
    """
    Returns the current month and year as a string in 'Month_Year' format.
    """
    return datetime.now().strftime("%d-%m-%Y_%H:%M:%S")  # Example: '21-01-2025_12:00'

def get_number_of_tokens(input_str) -> int:
    "Number of tokens in the input string."
    return len(input_str)

def get_input_str_for_queries(queries_data: dict) -> str:
    """
    Constructs a single input string from a list of query dictionaries.

    Args:
        queries_list (list[dict]): A list of dictionaries where each dictionary 
            contains the query ID and associated data, including the question,
            baseline, and current response.

    Returns:
        str: A formatted string concatenating the question, baseline, and current response
        for each query in the list, separated by newlines.
    """
    input_str = ""
    for query_id, query in queries_data.items():
        question = query.get("question", "")
        baseline = query.get("baseline", "")
        current = query.get("current", "")

        # Concatenate the question, baseline, and current response with newline separators
        input_str += f"{question}\n{baseline}\n{current}\n"

    return input_str

def get_output_str_for_queries(scores_data: dict[dict]) -> str:
    """
    Constructs a single output string from a dictionary of query results.

    Args:
        scores_data (dict[dict]): A dictionary where each key is a query ID and
            each value is another dictionary containing the query's score and reason.

    Returns:
        str: A formatted string concatenating the score and reason for each query
        in the dictionary, separated by newlines.
    """
    output_str = ""

    for query_id, query_output in scores_data.get("scores", {}).items():
        # Each query_output is expected to be a dictionary with score and reason keys
        reason = query_output.get("reason", "")
        score = query_output.get("score", "")

        # Concatenate the reason and score with newline separators
        output_str += f"{reason}\n{score}\n"

    return output_str

def post_score_for_queries(payload: dict) -> dict:
    """
    Makes a POST request to the server with the provided payload and returns the response.

    Args:
        payload (dict): The payload to be sent in the POST request.

    Returns:
        dict: The response from the server.

    Raises:
        Exception: If an error occurs while making the request or if the request failed.
    """
    import inspect

    try:
        # Dynamically get the base URL
        base_url = request.host_url.rstrip('/')  # Removes the trailing slash from the host_url
        url = f"{base_url}/get-score-for-queries"
        print("Making POST request to:", url)

        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            print("Request was successful.")
            # print(response.json())
            return response.json()
        else:
            print(f"Request failed with status code {response.status_code}. ({inspect.currentframe().f_code.co_name})")
            raise Exception(f"Request failed with status code {response.status_code}")
    except Exception as e:
        print(f"An error occurred while making the POST request: {e}")
        raise Exception(f"Failed to make the POST request: {e}")
    