import json
import requests
from pprint import pprint
from typing import List, Dict
import concurrent.futures

from .constants import (
    LOCAL_HOST_URL,
    MODEL_NAME,
)
from .prompts import (
    SYSTEM_PROMPT,
    SUMMARY_CHECK_PROMPT
)
from .queues import (
        QueueManager
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
        "stream": False,
        "keep_alive": "30m",
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
        "stream": False,
        "keep_alive": "30m",
    }

    try:
        response = retrieve_response_from_endpoint(data)
    except Exception as e:
        print(f"Error in get_response_from_llm: {e}")
        # Add context to the exception
        raise Exception(f"Failed to get response from LLM: {e}") from e

    # print("\nResults:")
    # pprint(response)
    
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

def get_score_from_llm_temp(question: str, baseline: str, current: str):
    
    return {
        "score": 0,
        "reason": "Dummmy reason"
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

# temp function for testing
def get_score_data_temp(question: str, baseline: str, current: str, summary_accepted: bool) -> dict:
    print("\nCalculating score...")
    print("Question: ", question)
    # print("Baseline: ", baseline)
    # print("Current: ", current)
    # print("Summary Accepted: ", summary_accepted)

    import time
    time.sleep(5)

    return {
        "score": 10,
        "reason": "No reason"
    }

def process_single_item(item: dict) -> dict:
    """
    Process a single item to retrieve the score.

    Args:
        item (dict): The item to process.

    Returns:
        dict: The score for the item.
    """
    query_id = list(item.keys())[0]
    query_data = item.get(query_id, {})

    question = query_data.get("question", "")
    baseline = query_data.get("baseline", "")
    current = query_data.get("current", "")
    summary_accepted = query_data.get("summary_accepted", False)

    score_data = get_score_data(question, baseline, current, summary_accepted)
    # score_data = get_score_data(question, baseline, current, summary_accepted)

    return {query_id: score_data}

def process_items(items_list: list[dict]) -> dict:
    """
    Process the items in the list using multiprocessing and return the scores.

    Args:
        items_list (List[dict]): The list of items to process.

    Returns:
        Dict[str, dict]: The scores for each item.
    """
    scores_retrieved = {}

    # test seq processing
    # results = []
    # for item in items_list:
    #     results.append(process_single_item(item))

    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(process_single_item, items_list))

    for result in results:
        scores_retrieved.update(result)

    return scores_retrieved

def get_scores_for_queries(queries_list: List[dict], queue_manager: QueueManager) -> Dict[str, dict]:
    """
    Retrieve scores for a list of queries using the provided queue manager.

    Args:
        queries_list (List[dict]): A list of dictionaries where each dictionary
            contains the query ID and associated data, including the question,
            baseline, current response, and whether the summary is accepted.
            
            Example format:
            [
                {"query_id": {
                        "question": "question string",
                        "baseline": "baseline string",
                        "current": "current string",
                        "summary_accepted": true
                    },
                },
                ...
            ]

        queue_manager (QueueManager): An instance of QueueManager used to manage
            and process the queries.

    Returns:
        Dict[str, dict]: A dictionary mapping each query ID to its respective
        scoring result and associated details.
    """
    scores_data = {}
    
    while True:
        items = queue_manager.get_items_to_process()
        queue_manager.delete_empty_queues()

        # No items to process
        if not items:
            break
        
        # process the retreived items
        scores = process_items(items)

        # add the scores
        scores_data.update(scores)

        query_ids = [list(item.keys()) for item in queries_list][0]
        
        
        # if all queries scores have been retrieved
        print("Query ids ",query_ids)
        print("Scores data keys ", list(scores_data.keys()))

        if query_ids == list(scores_data.keys()):
            print("Breaking...")
            break
        
        # import time
        # time.sleep(2)
    return scores_data

    
