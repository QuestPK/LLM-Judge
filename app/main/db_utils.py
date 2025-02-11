
from pprint import pprint
import uuid

from app import mongo
from .constants import DEFAULT_MAX_TOKEN_LIMIT, MAX_PROJECTS_ALLOWED
from .utils import (
    get_number_of_tokens,
    post_score_for_queries,
    get_current_datetime,
    get_current_month_year,
    generate_unique_project_id
)

def update_key_token(email: str) -> tuple:
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
            {"email": email},  # Query to find the document
            {
                "$set": {"key_token": key_token}
            },  # Update the key_token field
            upsert=True,  # Insert if the document does not exist
        )

        qa_data_exist = mongo.db.credits.find_one({"key_token": key_token})

        if qa_data_exist:
            #     If the key_token is unique, update the document or create a new one
            result = mongo.db.qa_data.update_one(
                {"email": email},  # Query to find the document
                {
                    "$set": {"key_token": key_token, "email": email}
                },  # Update the key_token field
                upsert=True,  # Insert if the document does not exist
            )

        return result, key_token
    
def check_token_limit(input_usage_str: str, key_token: str) -> bool:
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
    user_data = mongo.db.credits.find_one({"key_token": key_token})

    if not user_data:
        # If the document doesn't exist, create it
        raise ValueError(f"Document not found for token: {key_token}")
    elif current_month_year not in user_data:
        # If the document exists but the current month's token usage is missing, update it
        mongo.db.credits.update_one({"key_token": key_token},
                                    {"$set": {current_month_year: {"token_used" : 0}}})
        tokens_used = 0
    else:
        # Retrieve the existing token limit for the current month
        tokens_used = user_data[current_month_year]["token_used"]

    print(f"\nTokens Used till now(including this request): {tokens_used + number_of_tokens}")
    # Compare input tokens with the stored limit
    return number_of_tokens + tokens_used <= DEFAULT_MAX_TOKEN_LIMIT

def update_usage(input_str: str, output_str: str, processing_time: float, key_token: str, avg_queue_time: float = 0.0) -> None:
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
    user_data = mongo.db.credits.find_one({"key_token": key_token})
    print("\nUser Data before update: ")
    pprint(user_data)

    if not user_data:
        # If the document doesn't exist, raise an error
        print(f"Document not found for token: {key_token}")
        raise ValueError(f"Document not found for token: {key_token}")

    # Initialize or update the current month's usage
    current_usage = user_data.get(current_month_year, {})
    updated_total_token_used = current_usage.get("token_used", 0) + total_tokens
    updated_number_of_requests = current_usage.get("number_of_requests", 0) + 1
    updated_input_token_used = current_usage.get("total_input_token", 0) + input_tokens
    updated_output_tokens_used = current_usage.get("total_output_token", 0) + output_tokens
    updated_processing_time = current_usage.get("total_processing_time", 0) + processing_time

    print(f"Upd Processing time: {updated_processing_time}, Request: {updated_number_of_requests}")
    # Prepare the update operation with calculated averages
    update_fields = {
        f"{current_month_year}.token_used": updated_total_token_used,
        f"{current_month_year}.number_of_requests": updated_number_of_requests,

        f"{current_month_year}.total_input_token": round(updated_input_token_used, 2),
        f"{current_month_year}.avg_input_token": round(updated_input_token_used / updated_number_of_requests, 2),

        f"{current_month_year}.total_output_token": round(updated_output_tokens_used,2),
        f"{current_month_year}.avg_output_token": round(updated_output_tokens_used / updated_number_of_requests, 2),

        f"{current_month_year}.last_request_processing_time": round(processing_time, 2),
        f"{current_month_year}.total_processing_time": round(updated_processing_time, 2),
        f"{current_month_year}.avg_processing_time": round(updated_processing_time / updated_number_of_requests, 2),
    }

    if avg_queue_time > 0:
        # Update the average queue time if provided
        updated_avg_queue_time = current_usage.get("total_queue_time", 0) + avg_queue_time

        update_fields[f"{current_month_year}.avg_queue_time"] = round(updated_avg_queue_time / updated_number_of_requests, 2)
        update_fields[f"{current_month_year}.total_queue_time"] = round(updated_avg_queue_time, 2)

    # Perform the update operation in the database
    print("\nUpdated Fields:")
    pprint(update_fields)
    mongo.db.credits.update_one({"key_token": key_token}, {"$set": update_fields})

def add_qa(key_token: str, project_identifier: str, qa_data: dict) -> None:
    """
    Adds a QA set to the specified project in the user's database entry. 
    Supports both project ID and project name as identifiers.

    Args:
        key_token (str): The user identifier.
        project_identifier (str): Either the project ID or project name.
        qa_data (dict): A dictionary containing the QA set and its set_id.

    Raises:
        ValueError: If the QA set with the same set_id already exists within the project.
        Exception: If the project is not found or any error occurs while adding the QA set.
    """
    print("qa_data: ")
    pprint(qa_data)

    qa_set = qa_data.get("qa_set")
    set_id = qa_data.get("set_id")

    if not qa_set or not set_id:
        raise ValueError("Both 'qa_set' and 'set_id' must be provided.")

    try:
        # Retrieve user data
        user_data = mongo.db.qa_data.find_one({"key_token": key_token})

        if not user_data:
            raise Exception(f"Document not found for user: {key_token}")

        projects = user_data.get("projects", {})

        if not projects:
            raise Exception(f"No projects found for user. Add projects first.")

        # Identify the correct project
        project_key = None
        for proj_id, project in projects.items():
            if proj_id == project_identifier or project.get("project_name") == project_identifier:
                project_key = proj_id
                break

        if not project_key:
            raise ValueError(f"Project '{project_identifier}' not found.")

        project = projects[project_key]

        # Initialize "qa_sets" if it does not exist in the project
        if "qa_sets" not in project:
            project["qa_sets"] = []

        # Check if the set_id already exists within this project
        existing_set = next((entry for entry in project["qa_sets"] if entry["set_id"] == set_id), None)

        if existing_set:
            raise ValueError(f"QA set with set_id '{set_id}' already exists in project '{project_identifier}'.")

        # Determine baseline status
        is_baseline = len(project["qa_sets"]) == 0

        # Add new QA set
        new_qa_set = {
            "set_id": set_id,
            "qa_set": qa_set,
            "last_updated": get_current_datetime(),
            "baseline": is_baseline
        }

        project["qa_sets"].append(new_qa_set)

        # Save updated projects data back to the database
        mongo.db.qa_data.update_one(
            {"key_token": key_token},
            {"$set": {f"projects.{project_key}.qa_sets": project["qa_sets"]}}
        )

    except Exception as e:
        print(f"An error occurred while adding QA: {e}")
        raise Exception(f"Failed to add QA: {e}")

def update_baseline(key_token: str, project_identifier: str, set_id: str) -> None:
    """
    Updates the baseline QA set for a specific project.

    Args:
        key_token (str): The user identifier.
        project_identifier (str): Either the project ID or project name.
        set_id (str): The ID of the QA set to be updated as the new baseline.

    Raises:
        ValueError: If the user, project, or set_id does not exist.
        Exception: If an error occurs while updating the baseline.
    """
    if not set_id:
        raise ValueError("'set_id' must be provided to update the baseline.")

    try:
        # Retrieve user data
        user_data = mongo.db.qa_data.find_one({"key_token": key_token})

        if not user_data:
            raise ValueError(f"No data found for {key_token}")

        projects = user_data.get("projects", {})

        if not projects:
            raise ValueError(f"No projects found for user. Add projects first.")

        # Identify the correct project
        project_key = None
        for proj_id, project in projects.items():
            if proj_id == project_identifier or project.get("project_name") == project_identifier:
                project_key = proj_id
                break

        if not project_key:
            raise ValueError(f"Project '{project_identifier}' not found.")

        project = projects[project_key]

        # Ensure the project has QA sets
        if "qa_sets" not in project or not project["qa_sets"]:
            raise ValueError(f"No QA sets found in project '{project_identifier}'.")

        # Check if the set_id exists in the project’s QA sets
        existing_set = next(
            (entry for entry in project["qa_sets"] if entry["set_id"] == set_id),
            None
        )

        if not existing_set:
            raise ValueError(f"Set ID '{set_id}' does not exist in project '{project_identifier}'.")

        # Reset all `baseline` flags to False within this project
        mongo.db.qa_data.update_one(
            {"key_token": key_token},
            {"$set": {f"projects.{project_key}.qa_sets.$[].baseline": False}}
        )

        # Set the new baseline
        mongo.db.qa_data.update_one(
            {"key_token": key_token, f"projects.{project_key}.qa_sets.set_id": set_id},
            {"$set": {f"projects.{project_key}.qa_sets.$.baseline": True}}
        )

    except Exception as e:
        print(f"An error occurred while updating the baseline: {e}")
        raise Exception(f"Failed to update the baseline: {e}")

def update_qa(key_token: str, project_identifier: str, qa_data: dict) -> None:
    """
    Updates an existing QA set within a specified project.

    Args:
        key_token (str): The user identifier.
        project_identifier (str): Either the project ID or project name.
        qa_data (dict): A dictionary containing the QA set to be updated. Must contain:
            - set_id: The ID of the QA set to be updated.
            - qa_set: The new QA set data.

    Raises:
        ValueError: If the user, project, or set_id does not exist.
        Exception: If an error occurs while updating the QA set.
    """
    qa_set = qa_data.get("qa_set")
    set_id = qa_data.get("set_id")

    if not qa_set or not set_id:
        raise ValueError("Both 'qa_set' and 'set_id' must be provided.")

    try:
        # Retrieve user data
        user_data = mongo.db.qa_data.find_one({"key_token": key_token})

        if not user_data:
            raise ValueError(f"No QA data found for user: {key_token}")

        projects = user_data.get("projects", {})

        if not projects:
            raise ValueError(f"No projects found for user. Add projects first.")

        # Identify the correct project
        project_key = None
        for proj_id, project in projects.items():
            if proj_id == project_identifier or project.get("project_name") == project_identifier:
                project_key = proj_id
                break

        if not project_key:
            raise ValueError(f"Project '{project_identifier}' not found.")

        project = projects[project_key]

        # Ensure the project has QA sets
        if "qa_sets" not in project or not project["qa_sets"]:
            raise ValueError(f"No QA sets found in project '{project_identifier}'.")

        # Locate the QA set within the project
        qa_sets = project["qa_sets"]
        qa_set_index = next((i for i, entry in enumerate(qa_sets) if entry["set_id"] == set_id), None)

        if qa_set_index is None:
            raise ValueError(f"Set ID '{set_id}' does not exist in project '{project_identifier}'.")

        # Update the QA set
        current_datetime = get_current_datetime()
        qa_sets[qa_set_index]["qa_set"] = qa_set
        qa_sets[qa_set_index]["last_updated"] = current_datetime

        # Save updated QA sets to the database
        mongo.db.qa_data.update_one(
            {"key_token": key_token},
            {"$set": {f"projects.{project_key}.qa_sets": qa_sets}}
        )

    except Exception as e:
        print(f"An error occurred while updating the QA set: {e}")
        raise Exception(f"Failed to update the QA set: {e}")
 
def compare_qa_sets(key_token: str, project_identifier: str, current_set_id: str, baseline_set_id: str = None) -> dict:
    """
    Compare two QA sets for a user within a specific project and return the comparison results.

    Args:
        key_token (str): User identifier.
        project_identifier (str): Either the project ID or project name.
        current_set_id (str): ID of the current QA set.
        baseline_set_id (str, optional): ID of the baseline QA set. If not provided, the baseline is auto-selected.

    Returns:
        dict: A dictionary containing the comparison scores.

    Raises:
        ValueError: If the user, project, or QA sets are not found.
        Exception: If an error occurs while comparing QA sets.
    """
    if not current_set_id:
        raise ValueError("'current_set_id' must be provided.")
    
    try:
        # Find user data by key_token
        user_data = mongo.db.qa_data.find_one({"key_token": key_token})
        if not user_data:
            raise ValueError(f"No QA data found for: {key_token}")

        projects = user_data.get("projects", {})
        if not projects:
            raise ValueError(f"No projects found for user: {key_token}")

        # Identify the correct project
        project_key = None
        for proj_id, project in projects.items():
            if proj_id == project_identifier or project.get("project_name") == project_identifier:
                project_key = proj_id
                break

        if not project_key:
            raise ValueError(f"Project '{project_identifier}' not found.")
        project = projects[project_key]

        # Ensure the project has QA sets
        qa_sets = project.get("qa_sets", [])
        if not qa_sets:
            raise ValueError(f"No QA sets found in project '{project_identifier}'.")

        # Retrieve baseline QA set
        baseline_set = None
        if baseline_set_id:
            baseline_set = next((qa_set for qa_set in qa_sets if qa_set["set_id"] == baseline_set_id), None)
        else:
            baseline_set = next((qa_set for qa_set in qa_sets if qa_set.get("baseline", False)), None)

        if not baseline_set:
            raise ValueError("Baseline QA set could not be found.")

        # Retrieve the current QA set
        current_set = next((qa_set for qa_set in qa_sets if qa_set["set_id"] == current_set_id), None)

        if not current_set:
            raise ValueError(f"Current QA set with set_id '{current_set_id}' could not be found.")

        # Both sets same
        if current_set == baseline_set:
            raise ValueError("Both the sets are identical.")

        current_set_ids = {qa_set['id'] for qa_set in current_set["qa_set"]}
        baseline_set_ids = {qa_set['id'] for qa_set in baseline_set["qa_set"]}

        if current_set_ids != baseline_set_ids:
            raise Exception("Question sets do not match.")

        # Create a dictionary for query data
        queries_data = {}
        for baseline_qa, current_qa in zip(baseline_set["qa_set"], current_set["qa_set"]):
            question_id = baseline_qa["id"]
            query = {
                "question": baseline_qa["question"],
                "baseline": baseline_qa["answer"],
                "current": current_qa["answer"]
            }
            queries_data[str(question_id)] = query

        # Prepare the payload for the POST request
        payload = {
            "queries_data": queries_data,
        }

        headers = {
            "Content-Type": "application/json",
            "key-token" : key_token
        }

        print("Payload:")
        pprint(payload)

        print("Headers")
        print(headers)

        scores_data = post_score_for_queries(payload, headers=headers)

        # Enrich the scores data with question, baseline, and current answers
        enriched_scores_data = {}
        for question_id, score_info in scores_data.get("scores", {}).items():
            query_info = queries_data.get(question_id, {})

            enriched_scores_data[question_id] = {
                "reason": score_info.get("reason", "No reason"),
                "score": score_info.get("score", 0),
                "question": query_info.get("question", ""),
                "baseline": query_info.get("baseline", ""),
                "current": query_info.get("current", "")
            }

        print("Updated Scores Data:")
        pprint(enriched_scores_data)

        return enriched_scores_data
    except Exception as e:
        print(f"An error occurred while comparing QA sets: {e}")
        raise Exception(f"Failed to compare QA sets: {e}")

# is_baseline = baseline_set.get("baseline", False)
# if not is_baseline:
#     raise ValueError(f"Set with set_id {baseline_set_id} is not baseline.")

def get_usage_details(key_token: str) -> dict:
    """
    Retrieve usage details for a given email and project ID for the current month.

    Args:
        key_token : user identifier

    Returns:
        dict: A dictionary containing the usage details for the current month.

    Raises:
        ValueError: If no data is found for the provided email and project ID.
        Exception: If an error occurs while retrieving usage details.
    """
    try:
        # Retrieve user data from the MongoDB collection
        user_data = mongo.db.credits.find_one({"key_token" : key_token})
        print("user_data in get_usage_details: ")
        pprint(user_data)

        if not user_data:
            # Raise an error if no data is found
            raise ValueError(f"No data found for user: {key_token}")

        # Get the current month and year in 'Month_Year' format
        current_datetime = get_current_month_year()

        # Return the usage details for the current month
        return user_data.get(current_datetime, {})
    except Exception as e:
        # Print and raise an exception if an error occurs
        print(f"An error occurred while getting usage details: {e}")
        raise Exception(f"Failed to get usage details: {e}")

def get_set_ids(key_token: str, project_identifier: str) -> list[dict]:
    """
    Retrieve all QA set IDs and their data for a given user within a specific project.

    Args:
        key_token (str): User identifier.
        project_identifier (str): Either the project ID or project name.

    Returns:
        List[Dict]: A list of dictionaries containing the QA set IDs and their corresponding QA sets.
    """
    # Find user data by key_token
    user_data = mongo.db.qa_data.find_one({"key_token": key_token})

    if not user_data:
        raise ValueError(f"No user found for: {key_token}")

    projects = user_data.get("projects", {})

    if not projects:
        raise ValueError(f"No projects found for user: {key_token}")

    # Identify the correct project
    project_key = None
    for proj_id, project in projects.items():
        if proj_id == project_identifier or project.get("project_name") == project_identifier:
            project_key = proj_id
            break

    if not project_key:
        raise ValueError(f"Project '{project_identifier}' not found.")

    project = projects[project_key]

    # Ensure the project has QA sets
    qa_sets = project.get("qa_sets", [])
    if not qa_sets:
        raise ValueError(f"No QA sets found in project '{project_identifier}'.")

    # Create a list of dictionaries containing the QA set IDs and their corresponding QA sets
    set_ids = [
        {
            "set_id": qa_set.get("set_id", None),  # QA set ID
            "qa_set": qa_set.get("qa_set", [])    # QA set data
        }
        for qa_set in qa_sets
    ]

    return set_ids

def get_project_ids(key_token: str) -> list[dict]:
    """
    Retrieve all project IDs and their data for a given user.

    Args:
        key_token (str): User identifier.

    Returns:
        List[Dict]: A list of dictionaries containing the project IDs and their corresponding project data.
    """
    # Find user data by key_token
    user_data = mongo.db.qa_data.find_one({"key_token": key_token})

    if not user_data:
        raise ValueError(f"No user found for: {key_token}")

    projects = user_data.get("projects", {})

    if not projects:
        raise ValueError(f"No projects found for user: {key_token}")

    # Create a list of dictionaries containing the project IDs and their corresponding project data
    project_ids = [
        {
            "project_id": project_id,  # Project ID
            "project_name": project.get("project_name", "-"),  # Project name
            "qa_sets": project.get("qa_sets", [])  # QA sets for the project
        }
        for project_id, project in projects.items()
    ]

    return project_ids

def get_specific_project_details(key_token: str, project_identifier: str) -> dict:
    """ 
    Retrieve the details of a specific project for a given user.

    Args:
        key_token (str): User identifier.
        project_identifier (str): Either the project ID or project name.

    Returns:
        Dict: A dictionary containing the project details.
    """
    # Find user data by key_token
    user_data = mongo.db.qa_data.find_one({"key_token": key_token})

    if not user_data:  
        raise ValueError(f"No user found for: {key_token}")

    projects = user_data.get("projects", {})

    if not projects:
        raise ValueError(f"No projects found for user: {key_token}")

    # Identify the correct project
    project_key = None
    for proj_id, project in projects.items():
        if proj_id == project_identifier or project.get("project_name") == project_identifier:
            project_key = proj_id
            break

    if not project_key:
        raise ValueError(f"Project '{project_identifier}' not found.")

    project = projects[project_key]

    return project

def create_project(key_token: str, project_name: str) -> dict:
    """
    Create a new project for a user with a unique 4-digit project ID.

    Args:  
        key_token (str): User identifier.
        project_name (str): Name of the project.

    Returns:
        dict: A dictionary containing the created project data.
    """
    # Retrieve user data from MongoDB
    user_data = mongo.db.qa_data.find_one({"key_token": key_token})
    
    if not user_data:
        raise ValueError(f"No user found for: {key_token}")

    # Maximum number of projects allowed
    if len(user_data.get("projects", {})) >= MAX_PROJECTS_ALLOWED:
        raise ValueError("You have reached the maximum number of projects.")
    
    # Initialize the "projects" field if it doesn't exist
    if "projects" not in user_data:
        user_data["projects"] = {}

    # Check for duplicate project names
    existing_project_names = {proj["project_name"] for proj in user_data["projects"].values()}
    
    if project_name in existing_project_names:
        raise ValueError(f"A project with the name '{project_name}' already exists.")

    # Extract existing project IDs
    existing_project_ids = set(user_data["projects"].keys())

    # Generate a unique 4-digit project ID
    project_id = generate_unique_project_id(existing_project_ids)

    # Create the new project
    new_project = {
        f"{project_id}" : {
            "project_name" : project_name
        }
    }
    
    # Append the new project
    user_data["projects"].update(new_project)

    # Save to the database (only updating the projects field)
    mongo.db.qa_data.update_one(
        {"key_token": key_token},
        {"$set": {"projects": user_data["projects"]}}
    )

    return new_project

def delete_project(key_token: str, project_id: str) -> None:
    """
    Delete a project for a user.

    Args:
        key_token (str): User identifier.
        project_id (str): ID of the project to delete.

    Raises:
        ValueError: If the user or project is not found.
    """
    # Find user data
    user_data = mongo.db.qa_data.find_one({"key_token": key_token})

    if not user_data:
        raise ValueError(f"No user found for: {key_token}")

    # Find the project to delete
    project_to_delete = next((proj for proj_id, proj in user_data["projects"].items() if proj_id == project_id), None)

    if not project_to_delete:
        raise ValueError(f"Project with ID {project_id} not found.")

    # Delete the project
    del user_data["projects"][project_id]

    # Save to the database (only updating the projects field)
    mongo.db.qa_data.update_one(
        {"key_token": key_token},
        {"$set": {"projects": user_data["projects"]}}
    )

def update_project_name(key_token: str, project_id: str, project_name: str) -> None:
    """
    Update the name of a project for a user.

    Args:
        key_token (str): User identifier.
        project_id (str): ID of the project to update.
        project_name (str): New name for the project.

    Raises:
        ValueError: If the user or project is not found.
    """
    # Find user data
    user_data = mongo.db.qa_data.find_one({"key_token": key_token})

    if not user_data:  
        raise ValueError(f"No user found for: {key_token}")

    # Find the project to update
    project_to_update = next((proj for proj_id, proj in user_data["projects"].items() if proj_id == project_id), None)

    if not project_to_update:
        raise ValueError(f"Project with ID {project_id} not found.")

    # Update the project name
    project_to_update["project_name"] = project_name

    # Save to the database (only updating the projects field)
    mongo.db.qa_data.update_one(
        {"key_token": key_token},
        {"$set": {"projects": user_data["projects"]}}
    )

def delete_qa_set(key_token: str, project_identifier: str, set_id: int) -> None:
    """
    Delete a QA set for a user unless it's a baseline.

    Args:
        key_token (str): User identifier.
        project_identifier (str): Either the project ID or project name.
        set_id (int): ID of the QA set to delete.

    Raises:
        ValueError: If the user, project, or QA set is not found, or if the set is a baseline.
    """
    # Fetch user data
    user_data = mongo.db.qa_data.find_one({"key_token": key_token})
    if not user_data:
        print("No user data found for key_token:", key_token)
        raise ValueError(f"User not found!")

    # Fetch project data
    project_to_update = user_data.get("projects", {}).get(project_identifier)
    if not project_to_update:
        raise ValueError(f"Project '{project_identifier}' not found for user.")

    # Find the QA set
    for qa_set in project_to_update["qa_sets"]:
        if qa_set["set_id"] == set_id:
            if qa_set.get("baseline", False):
                raise ValueError(f"Baseline QA set cannot be deleted.")
            
            # Remove the QA set
            project_to_update["qa_sets"] = [
                s for s in project_to_update["qa_sets"] if s["set_id"] != set_id
            ]

            # Update the database only if deletion occurs
            mongo.db.qa_data.update_one(
                {"key_token": key_token},
                {"$set": {"projects": user_data["projects"]}}
            )
            return

    raise ValueError(f"QA set with ID {set_id} not found in project '{project_identifier}'.")

def save_qa_scores(key_token: str, set_id: int, project_identifier: str, qa_scores: dict):
    # Fetch user data
    user_data = mongo.db.qa_data.find_one({"key_token": key_token})
    if not user_data:
        raise ValueError(f"No user data found for key_token: {key_token}")

    # Check if the project exists for the user
    project_data = user_data.get("projects", {}).get(project_identifier)
    if not project_data:
        raise ValueError(f"Project '{project_identifier}' not found for user.")

    # Get the QA sets list
    qa_sets_list = project_data.get("qa_sets", [])
    
    # Locate the specific QA set by its set_id
    for qa_set in qa_sets_list:
        if qa_set.get("set_id") == set_id:
            # Update the QA set with the scores
            qa_set["scores"] = qa_scores
            break
    else:
        raise ValueError(f"Set does does not exist in this project.")
    
    # Save updated QA sets back to the database
    mongo.db.qa_data.update_one(
        {"key_token": key_token},
        {"$set": {f"projects.{project_identifier}.qa_sets": qa_sets_list}}
    )

def get_set_scores(key_token:str, set_id:int, project_id:str) -> dict:
    # Fetch user data
    user_data = mongo.db.qa_data.find_one({"key_token": key_token})
    if not user_data:
        raise ValueError(f"No user data found for key_token: {key_token}")

    # Check if the project exists for the user
    project_data = user_data.get("projects", {}).get(project_id)
    if not project_data:
        raise ValueError(f"Project '{project_id}' not found for user.")

    qa_sets_data = project_data.get("qa_sets", [])
    for qa_set in qa_sets_data:
        print(set_id, type(set_id))
        pprint(qa_set)
        if qa_set.get("set_id", 0) == set_id:
            print(qa_set.get("set_id", 0) == set_id)
            return qa_set.get("scores")
    
    raise ValueError("No previous scores data found.")