from datetime import datetime
from pprint import pprint
import uuid
from app import mongo
from .constants import DEFAULT_MAX_TOKEN_LIMIT

def get_number_of_tokens(input_str) -> int:
    return len(input_str)

def get_current_month_year() -> str:
    """
    Returns the current month and year as a string in 'Month_Year' format.
    """
    return datetime.now().strftime("%B_%Y")  # Example: 'January_2025'

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

    for query_id, query_output in scores_data.items():
        # Each query_output is expected to be a dictionary with score and reason keys
        reason = query_output.get("reason", "")
        score = query_output.get("score", "")

        # Concatenate the reason and score with newline separators
        output_str += f"{reason}\n{score}\n"

    return output_str


def update_key_token(email: str):
    """
    Updates the `key_token` field for a given email, ensuring the `key_token` is unique across the entire collection.

    Args:
        email (str): The email of the document to update.

    Returns:
        UpdateResult: The result of the update operation.
    """
    while True:
        # Generate a new unique key_token
        key_token = str(uuid.uuid4())

        # Check if the key_token already exists in the collection
        existing_token = mongo.db.credits.find_one({"key_token": key_token})

        if not existing_token:
            # If the key_token is unique, update the document with the new key_token
            result = mongo.db.credits.update_one(
                {"email": email},  # Query to find the document
                {
                    "$set": {"key_token": key_token}
                },  # Update the key_token field
                upsert=True,  # Insert if the document does not exist
            )
            return result, key_token
    
def check_token_limit(input_usage_str: str, email: str) -> bool:
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
    user_data = mongo.db.credits.find_one({"email": email})

    if not user_data:
        # If the document doesn't exist, create it
        mongo.db.credits.insert_one({"email": email, current_month_year: {"token_used" : 0}})
        tokens_used = 0
    elif current_month_year not in user_data:
        # If the document exists but the current month's token usage is missing, update it
        mongo.db.credits.update_one({"email": email}, {"$set": {current_month_year: {"token_used" : 0}}})
        tokens_used = 0
    else:
        # Retrieve the existing token limit for the current month
        tokens_used = user_data[current_month_year]["token_used"]

    print("\nTokens Used till now: ", tokens_used + number_of_tokens)
    # Compare input tokens with the stored limit
    return number_of_tokens + tokens_used <= DEFAULT_MAX_TOKEN_LIMIT

def update_usage(input_str: str, output_str: str, email: str) -> None:
    """
    Updates the database with the token usage for the current month and increments the number of requests.
    If the email document or the required fields are not present, it raises an error.

    Args:
        input_str (str): The input string.
        output_str (str): The output string.
        email (str): The email for which the usage is being updated.

    Returns:
        None
    """
    # Calculate tokens for input and output strings
    input_tokens = get_number_of_tokens(input_str)
    output_tokens = get_number_of_tokens(output_str)
    total_tokens = input_tokens + output_tokens

    # Get the field name for the current month and year
    current_month_year = get_current_month_year()

    # Retrieve the document for the email
    user_data = mongo.db.credits.find_one({"email": email})
    print("User Data: ")
    pprint(user_data)

    if not user_data:
        # If the document doesn't exist, raise an error
        print("Document not found for email:", email)
        raise ValueError(f"Document not found for email: {email}")

    # Initialize or update the current month's usage
    current_usage = user_data.get(current_month_year, {})
    updated_token_used = current_usage.get("token_used", 0) + total_tokens
    updated_number_of_requests = current_usage.get("number_of_requests", 0) + 1

    # Prepare the update operation
    update_fields = {
        f"{current_month_year}.token_used": updated_token_used,
        f"{current_month_year}.number_of_requests": updated_number_of_requests,
    }

    # Perform the update
    print("\nUpdated Fields:")
    pprint(update_fields)
    mongo.db.credits.update_one({"email": email}, {"$set": update_fields})


