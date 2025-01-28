from datetime import datetime
from pprint import pprint
import uuid

from flask import request
import requests

from app import mongo
from .constants import DEFAULT_MAX_TOKEN_LIMIT

def get_number_of_tokens(input_str) -> int:
    "Number of tokens in the input string."
    return len(input_str)

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

def get_input_str_for_queries(queries_list: list[dict]) -> str:
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

    for query_data in queries_list:
        # Each query_data is expected to be a dictionary with a single key-value pair
        for query_id, query in query_data.items():
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

def update_key_token(email: str, project_id: int):
    """
    Updates the `key_token` field for a given email, ensuring the `key_token` is unique across the entire collection.

    Args:
        email (str): The email of the document to update.
        project_id (int): The project ID associated with the email.

    Returns:
        tuple: The result of the update operation and the generated key_token.
    """
    while True:
        # Generate a new unique key_token
        key_token = str(uuid.uuid4())

        # Check if the key_token already exists in the collection
        existing_token = mongo.db.credits.find_one({"key_token": key_token})
        if existing_token:
            # If the key_token already exists, retry with a new token
            continue

        # If the key_token is unique, update the document or create a new one
        result = mongo.db.credits.update_one(
            {"email": email, "project_id": project_id},  # Query to find the document
            {
                "$set": {"key_token": key_token}
            },  # Update the key_token field
            upsert=True,  # Insert if the document does not exist
        )
        return result, key_token
    
def check_token_limit(input_usage_str: str, email: str, project_id: int) -> bool:
    """
    Checks if the number of tokens in input_usage_str exceeds the token usage for the current month.
    Creates or updates the document if email or current month's token limit is missing.

    Args:
        input_usage_str (str): The input string for which tokens are calculated.
        email (str): The email used to retrieve or initialize the token limit.

    Returns:
        bool: True if the token usage is within the limit, False otherwise.
    """
    # Calculate tokens from the input string
    number_of_tokens = get_number_of_tokens(input_usage_str)

    # Get the field name for the current month and year
    current_month_year = get_current_month_year()

    # Ensure the email document exists and has the current month's token limit
    user_data = mongo.db.credits.find_one({"email": email, "project_id" : project_id})

    if not user_data:
        # If the document doesn't exist, create it
        raise ValueError(f"Document not found for email: {email} and project_id: {project_id}")
    elif current_month_year not in user_data:
        # If the document exists but the current month's token usage is missing, update it
        mongo.db.credits.update_one({"email": email, "project_id" : project_id},
                                    {"$set": {current_month_year: {"token_used" : 0}}})
        tokens_used = 0
    else:
        # Retrieve the existing token limit for the current month
        tokens_used = user_data[current_month_year]["token_used"]

    print(f"\nTokens Used till now(including this request): {tokens_used + number_of_tokens}")
    # Compare input tokens with the stored limit
    return number_of_tokens + tokens_used <= DEFAULT_MAX_TOKEN_LIMIT

def update_usage(input_str: str, output_str: str, processing_time: float, email: str, project_id: int, avg_queue_time: float = 0.0) -> None:
    """
    Updates the database with the token usage for the current month, increments the number of requests, 
    and updates average processing and queue times.
    
    If the email document or the required fields are not present, it raises an error.

    Args:
        input_str (str): The input string for which tokens are calculated.
        output_str (str): The output string for which tokens are calculated.
        processing_time (float): The time taken to process the request.
        email (str): The email for which the usage is being updated.
        project_id (int): The project ID associated with the email.
        avg_queue_time (float, optional): The average time spent in the queue. Defaults to 0.0.

    Returns:
        None
    """
    print("\nUpdating usage...")

    # Calculate tokens for input and output strings
    input_tokens = get_number_of_tokens(input_str)
    output_tokens = get_number_of_tokens(output_str)
    total_tokens = input_tokens + output_tokens

    # Get the field name for the current month and year
    current_month_year = get_current_month_year()

    # Retrieve the document for the email and project_id
    user_data = mongo.db.credits.find_one({"email": email, "project_id": project_id})
    print("\nUser Data before update: ")
    pprint(user_data)

    if not user_data:
        # If the document doesn't exist, raise an error
        print(f"Document not found for email: {email} and project_id: {project_id}")
        raise ValueError(f"Document not found for email: {email} and project_id: {project_id}")

    # Initialize or update the current month's usage
    current_usage = user_data.get(current_month_year, {})
    updated_total_token_used = current_usage.get("token_used", 0) + total_tokens
    updated_input_token_used_per_request = current_usage.get("avg_input_token", 0) + input_tokens
    updated_output_tokens_used_per_request = current_usage.get("avg_output_token", 0) + output_tokens
    updated_number_of_requests = current_usage.get("number_of_requests", 0) + 1
    updated_processing_time = current_usage.get("avg_processing_time", 0) + processing_time

    # Prepare the update operation with calculated averages
    update_fields = {
        f"{current_month_year}.token_used": updated_total_token_used,
        f"{current_month_year}.avg_input_token": round(updated_input_token_used_per_request / updated_number_of_requests, 2),
        f"{current_month_year}.avg_output_token": round(updated_output_tokens_used_per_request / updated_number_of_requests, 2),
        f"{current_month_year}.number_of_requests": updated_number_of_requests,
        f"{current_month_year}.processing_time": round(processing_time, 2),
        f"{current_month_year}.avg_processing_time": round(updated_processing_time / updated_number_of_requests, 2),
    }

    if avg_queue_time > 0:
        # Update the average queue time if provided
        updated_avg_queue_time = current_usage.get("avg_queue_time", 0) + avg_queue_time
        update_fields[f"{current_month_year}.avg_queue_time"] = round(updated_avg_queue_time / updated_number_of_requests, 2)

    # Perform the update operation in the database
    print("\nUpdated Fields:")
    pprint(update_fields)
    mongo.db.credits.update_one({"email": email, "project_id": project_id}, {"$set": update_fields})

def add_qa(email: str, project_id: str, qa_data: dict) -> None:
    """
    Adds a QA set to the user's database entry. If the QA set with the same set_id already exists, raises a ValueError.

    Args:
        email (str): The email address of the user who owns the QA set.
        qa_data (dict): A dictionary containing the QA set and its set_id.

    Raises:
        ValueError: If the QA set with the same set_id already exists.
        Exception: If an error occurs while adding the QA set.
    """
    qa_set = qa_data.get("qa_set")
    set_id = qa_data.get("set_id")

    if not qa_set or not set_id:
        raise ValueError("Both 'qa_set' and 'set_id' must be provided.")

    try:
        # Retrieve the user's current QA sets
        user_data = mongo.db.credits.find_one({"email": email, "project_id": project_id})

        if not user_data:
            raise Exception(f"Document not found for email: {email} and project_id: {project_id}")

        user_data = mongo.db.qa_data.find_one({"email": email, "project_id": project_id})
        if not user_data.get("qa_sets"):
            print("First QA Set.")
            # If this is the first QA set, add it as the baseline
            mongo.db.qa_data.insert_one({
                "email": email,
                "project_id" : project_id,
                "qa_sets": [
                    {
                        "set_id": set_id,
                        "qa_set": qa_set,
                        "last_updated": get_current_datetime(),
                        "baseline": True
                    }
                ]
            })
        else:
            # Check if the set_id already exists
            existing_set = next(
                (entry for entry in user_data.get("qa_sets", []) if entry["set_id"] == set_id),
                None
            )

            if existing_set:
                # Update the existing QA set is not possible
                raise ValueError("QA set with the same set_id already exists.")
            else:
                # Add the new QA set with baseline set to False
                current_datetime = get_current_datetime()
                mongo.db.qa_data.update_one(
                    {"email": email, "project_id" : project_id},
                    {"$push": {
                        "qa_sets": {
                            "set_id": set_id,
                            "qa_set": qa_set,
                            "last_updated": current_datetime,
                            "baseline": False
                        }
                    }}
                )
    except Exception as e:
        print(f"An error occurred while adding QA: {e}")
        raise Exception(f"Failed to add QA: {e}")

def update_baseline(email: str, project_id: str, set_id: str) -> None:
    """
    Updates the baseline QA set for the given user.

    Args:
        email (str): The email address of the user who owns the QA set.
        set_id (str): The ID of the QA set to be updated as the new baseline.

    Raises:
        ValueError: If the email address is not found in the database or if the set_id does not exist for the given email.
        Exception: If an error occurs while updating the baseline.
    """
    if not set_id:
        raise ValueError("'set_id' must be provided to update the baseline.")

    try:
        user_data = mongo.db.credits.find_one({"email": email, "project_id" : project_id})

        if not user_data:
            raise ValueError(f"No data found for email: {email} and project: {project_id}")

        # Check if the set_id exists in the user's data
        existing_set = next(
            (entry for entry in user_data.get("qa_sets", []) if entry["set_id"] == set_id),
            None
        )

        if not existing_set:
            raise ValueError(f"Set ID '{set_id}' does not exist for email: {email}")

        # Reset all `baseline` flags to False
        # This is done by updating all `qa_sets` subdocuments in the user's data
        mongo.db.qa_data.update_many(
            {"email": email},
            {"$set": {"qa_sets.$[].baseline": False}}
        )

        # Update the provided set_id to be the new baseline
        # This is done by updating the specific `qa_sets` subdocument with the given set_id
        mongo.db.qa_data.update_one(
            {"email": email, "project_id" : project_id, "qa_sets.set_id": set_id},
            {"$set": {"qa_sets.$.baseline": True}}
        )

    except Exception as e:
        print(f"An error occurred while updating the baseline: {e}")
        raise Exception(f"Failed to update the baseline: {e}")

def update_qa(email: str, project_id: str, qa_data: dict) -> None:
    """
    Updates an existing QA set.

    Args:
        email (str): The email address of the user who owns the QA set.
        qa_data (dict): The dictionary containing the QA set to be updated. Must contain the keys 'qa_set' and 'set_id'.
            qa_set: The QA set to be updated.
            set_id: The ID of the QA set to be updated.

    Raises:
        ValueError: If the email address is not found in the database or if the set_id does not exist for the given email.
        Exception: If an error occurs while updating the QA set.
    """
    qa_set = qa_data.get("qa_set")
    set_id = qa_data.get("set_id")

    if not qa_set or not set_id:
        raise ValueError("Both 'qa_set' and 'set_id' must be provided.")

    try:
        # Find user data by email
        user_data = mongo.db.credits.find_one({"email": email, "project_id" : project_id})

        if not user_data:
            raise ValueError(f"No data found for email: {email} and project id: {project_id}")

        # Check if the set_id exists in the user's QA sets
        existing_set = next(
            (entry for entry in user_data.get("qa_sets", []) if entry["set_id"] == set_id),
            None
        )
        if not existing_set:
            raise ValueError(f"Set ID '{set_id}' does not exist for email: {email} and project id: {project_id}")

        # Update the QA set and the last_updated timestamp
        current_datetime = get_current_datetime()
        mongo.db.qa_data.update_one(
            {"email": email, "project_id" : project_id, "qa_sets.set_id": set_id},
            {
                "$set": {
                    "qa_sets.$.qa_set": qa_set,
                    "qa_sets.$.last_updated": current_datetime
                }
            }
        )

    except Exception as e:
        print(f"An error occurred while updating the QA set: {e}")
        raise Exception(f"Failed to update the QA set: {e}")
    
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
    
def compare_qa_sets(email: str, project_id: str, current_set_id: str, baseline_set_id: str = None) -> None:
    if not current_set_id:
        raise ValueError("'current_set_id' must be provided.")
    
    try:
        # Find user data by email and project_id
        user_data = mongo.db.qa_data.find_one({"email": email, "project_id": project_id})
        
        if not user_data:
            raise ValueError(f"No data found for email: {email} and project id: {project_id}")
        
        # Retrieve baseline QA set
        baseline_set = None
        if baseline_set_id:
            # Find the baseline set using the provided `baseline_set_id`
            baseline_set = next(
                (qa_set for qa_set in user_data["qa_sets"] if qa_set["set_id"] == int(baseline_set_id)), 
                None
            )
        else:
            # Find the baseline set where `baseline` is True
            baseline_set = next(
                (qa_set for qa_set in user_data["qa_sets"] if qa_set.get("baseline", False)), 
                None
            )
        
        if not baseline_set:
            raise ValueError("Baseline QA set could not be found.")
        
        # Retrieve the current QA set
        current_set = next(
            (qa_set for qa_set in user_data["qa_sets"] if qa_set["set_id"] == int(current_set_id)), 
            None
        )
        
        if not current_set:
            raise ValueError(f"Current QA set with set_id {current_set_id} could not be found.")
        
        # Both sets same
        if current_set == baseline_set:
            raise ValueError("Both the sets are identical.")
        
        current_set_ids = set([qa_set['id'] for qa_set  in current_set["qa_set"]])
        baseline_set_ids = set([qa_set['id'] for qa_set  in baseline_set["qa_set"]])

        if not current_set_ids == baseline_set_ids:
            raise Exception("Questions sets are not same.")
        
        # print("Current set ids: ", current_set_ids)
        # print("Baseline set ids: ", baseline_set_ids)

        baseline_qa_set = baseline_set.get('qa_set')
        current_qa_set = current_set.get('qa_set')

        # Create a dictionary for query data
        queries_data = {}
        
        # Loop through questions in the baseline and current sets
        for baseline_qa, current_qa in zip(baseline_qa_set, current_qa_set):
            question_id = baseline_qa["id"]
            query = {
                "question": baseline_qa["question"],
                "baseline": baseline_qa["answer"],
                "current": current_qa["answer"]
            }
            queries_data[str(question_id)] = query
        
        # Prepare the payload for the POST request
        payload = {
            "queries_data": [queries_data],
            "email": email,
            "project_id" : project_id
        }
        print("payload")
        pprint(payload)

        scores_data = post_score_for_queries(payload)

        # Now, include the question, baseline, and current answers into the scores_data
        enriched_scores_data = {}
        
        for question_id, score_info in scores_data.get("scores_data").items():
            # Retrieve the query details for the question ID
            query_info = queries_data.get(question_id, {})

            # Add the question, baseline, and current answers to the score data
            enriched_scores_data[question_id] = {
                "reason": score_info.get("reason", "No reason"),
                "score": score_info.get("score", 0),
                "question": query_info.get("question", ""),
                "baseline": query_info.get("baseline", ""),
                "current": query_info.get("current", "")
            }
        
        # You can now work with the enriched_scores_data that includes the question, baseline, current, reason, and score
        print("\nEnriched Scores Data:")
        pprint(enriched_scores_data)

        return enriched_scores_data
    except Exception as e:
        print(f"An error occurred while comparing QA sets: {e}")
        raise Exception(f"Failed to compare QA sets: {e}")

def get_usage_details(email: str, project_id: int) -> dict:
    """
    Retrieve usage details for a given email and project ID for the current month.

    Args:
        email (str): The email address of the user.
        project_id (int): The project ID associated with the user.

    Returns:
        dict: A dictionary containing the usage details for the current month.

    Raises:
        ValueError: If no data is found for the provided email and project ID.
        Exception: If an error occurs while retrieving usage details.
    """
    try:
        # Retrieve user data from the MongoDB collection
        user_data = mongo.db.credits.find_one({"email": email, "project_id": project_id})
        print("user_data in get_usage_details: ")
        pprint(user_data)

        if not user_data:
            # Raise an error if no data is found
            raise ValueError(f"No data found for email: {email} and project id: {project_id}")

        # Get the current month and year in 'Month_Year' format
        current_datetime = get_current_month_year()

        # Return the usage details for the current month
        return user_data.get(current_datetime, {})
    except Exception as e:
        # Print and raise an exception if an error occurs
        print(f"An error occurred while getting usage details: {e}")
        raise Exception(f"Failed to get usage details: {e}")
