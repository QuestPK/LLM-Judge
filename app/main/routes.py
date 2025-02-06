import uuid
from pprint import pprint
import time

from flask import Blueprint, request
from flask_restx import Resource, fields, Namespace

from app.extensions import api
from .judge_utilities import get_score_data, get_scores_for_queries, get_score_from_rag
from .db_utils import (
    update_key_token,
    update_usage,
    check_token_limit,
    add_qa,
    update_baseline,
    update_qa,
    delete_qa_set,
    compare_qa_sets,
    get_usage_details,
    get_set_ids,
    get_project_ids,
    get_specific_project_details,
    create_project,
    delete_project,
    update_project_name,
)
from .utils import get_input_str_for_queries, get_output_str_for_queries
from .queues import queue_manager
from .swagger_models import * 

main_bp = Blueprint("main", __name__)

judge_ns = Namespace(
    name="Judge",
    description="Judge NS",
    path='/'
)
api.add_namespace(judge_ns)

@judge_ns.route("/create-key-token")
class CreateKeyToken(Resource):
    @api.expect(input_create_key_token_model)
    @api.doc(
        description="Retrieve and create a unique key token for a given email.",
    )
    @api.response(200, "Success", output_create_key_token_model)
    @api.response(
        400, "Quota exceeded / Invalid input / Not found", error_response_model
    )
    @api.response(500, "Internal Server Error", error_response_model)
    def post(self):
        """
        Retrieve and create a unique key token for a given email. It will create a new data document if the email is not found.
        - **email**: User's email address.
        """
        data = request.get_json()

        if not data or "email" not in data:
            return {"error": "Invalid input, 'email' key is required"}, 400

        email = data["email"]

        try:
            result, new_key_token = update_key_token(email)
        except Exception as e:
            return {"error": str(e)}, 500
        
        if result.matched_count > 0:
            message = "Email found. key_token updated."
        else:
            message = "Email not found. New document added."

        print(
            {
                "message": message,
                "email": email,
                "key_token": new_key_token,
            }
        )
        return {
            "message": message,
            "key_token": new_key_token,
        }, 200

# Route for adding a new QA set
@judge_ns.route("/add-qna")
class AddQnA(Resource):
    @api.expect(input_add_qa_request_model)
    @api.doc(
        description="Add a new QA set for a given email.",
        params={
            "key-token": {
                "description": "User identification token",
                "in": "header",
                "type": "string",
                "required": True,
            }
        },
    )
    @api.response(200, "Success", add_qna_output_model)
    @api.response(400, "Invalid input / Not found", error_response_model)
    @api.response(500, "Internal Server Error", error_response_model)
    def post(self):
        """
        Adds a new QA set for the given email.
        - **qa_data**: QA data object with set_id
        """
        key_token = request.headers.get("key-token")
        if not key_token:
            return {"error": "Missing key token."}, 400

        data = request.get_json()
        if not data or ("project_id" not in data and "qa_data" not in data):
            return {"error": "Invalid input, required parameter is missing"}, 400

        qa_data = data["qa_data"]
        project_id = data["project_id"]

        try:
            # adding QA to db
            add_qa(key_token=key_token, project_identifier=project_id, qa_data=qa_data)
            print(f"QA set added against: {key_token} successfully.")
            return {"response": f"QA set added successfully."}, 200
        except Exception as e:
            print(f"Error in /set-qa: {str(e)}")
            return {"error": str(e)}, 400

@judge_ns.route("/set-baseline")
class SetBaseline(Resource):
    @api.expect(input_set_baseline_model)
    @api.doc(
        description="Set provided set as a baseline for a given email and project id.",
        params={
            "key-token": {
                "description": "User identification token",
                "in": "header",
                "type": "string",
                "required": True,
            }
        },
    )
    @api.response(200, "Success", success_response_model)  # Success response
    @api.response(
        400, "Invalid input / Not found", error_response_model
    )  # Invalid input or not found
    @api.response(500, "Internal Server Error", error_response_model)  # Server error
    def put(self):
        """
        Update the baseline to the given set ID.
        - **set_id**: QA set ID
        """
        key_token = request.headers.get("key-token")
        if not key_token:
            return {"error": "Missing key token."}, 400

        data = request.get_json()
        if not data or ("set_id" not in data and "project_id" not in data):
            return {"error": "Invalid input, required parameter is missing"}, 400

        set_id = data["set_id"]
        project_id = data["project_id"]

        try:
            # setting baseline (replace this with your actual logic)
            update_baseline(
                key_token=key_token, project_identifier=project_id, set_id=set_id
            )
            return {"response": f"Baseline updated against: {key_token}"}, 200
        except ValueError as e:
            # Assuming a custom exception like ValueError for this case
            return {"error": f"Error: {str(e)}"}, 400
        except Exception as e:
            # Handling any general exceptions
            print("Error in /set-baseline:", str(e))
            return {"error": f"{str(e)}"}, 500

@judge_ns.route("/update-qna")
class UpdateQnA(Resource):
    @api.expect(input_update_qa_model)
    @api.doc(
        description="Update an existing QA set for a given user.",
        params={
            "key-token": {
                "description": "User identification token",
                "in": "header",
                "type": "string",
                "required": True,
            }
        },
    )
    @api.response(200, "Success", success_qa_model)
    @api.response(400, "Invalid input / Not found", error_response_model)
    @api.response(500, "Internal Server Error", error_response_model)
    def put(self):
        """
        Update an existing QA set for a given email.
        - **qa_data**: QA data object with set_id
        """
        key_token = request.headers.get("key-token")
        if not key_token:
            return {"error": "Missing key token."}, 400

        # Get JSON data from the request
        data = request.get_json()

        # Input parameter validation
        if not data or "qa_data" not in data or "project_id" not in data:
            return {"error": "Invalid input, required parameter is missing"}, 400

        qa = data["qa_data"]
        project_id = data["project_id"]

        try:
            # Attempt to update the QA set
            update_qa(key_token=key_token, project_identifier=project_id, qa_data=qa)
        except Exception as e:
            print("Error in /update-qa route:", e)
            return {"error": f"{str(e)}"}, 400

        return {"response": f"QA set updated against: {key_token} successfully."}, 200

@api.route("/calculate-score")
class CalculateScore(Resource):
    @api.expect(calculate_score_model)
    @api.doc(
        description="Calculate the score for a given question, baseline, and current text.",
        params={
            "key-token": {
                "description": "User identification token",
                "in": "header",
                "type": "string",
                "required": True,
            }
        },
    )
    @api.response(200, "Success", output_score_model)
    @api.response(
        400, "Quota exceeded / Invalid input / Not found", error_response_model
    )
    @api.response(500, "Internal Server Error", error_response_model)
    def post(self):
        """
        Calculate the score for a given question, baseline, and current text.
        - **query_data**: Object containing the question, baseline, and current text.
        - **summary_accepted (Optional)**: Whether the summary is accepted or not.
        """
        key_token = request.headers.get("key-token")
        if not key_token:
            return {"error": "Missing key token."}, 400

        data = request.get_json()

        if data is None:
            return {"error": "No valid JSON data found in the request."}, 400

        if "query_data" not in data:
            return {"error": "Invalid, input parameters missing."}, 400

        query_data = data.get("query_data")

        question = query_data.get("question", "")
        baseline = query_data.get("baseline", "")
        current = query_data.get("current", "")
        summary_accepted = data.get("summary_accepted", False)

        if not baseline or not current or not question:
            return {"error": "Baseline or Current missing."}, 400

        try:
            input_usage_str = f"{question}\n{baseline}\n{current}"
            try:
                is_under_limit = check_token_limit(
                    input_usage_str=input_usage_str, key_token=key_token
                )
            except Exception as e:
                return {"error": str(e)}, 400

            if not is_under_limit:
                return {
                    "error": "You have used the max number of tokens allowed this month. Please try again later."
                }, 400

            start_time = time.time()
            score_data = get_score_data(
                question=question,
                baseline=baseline,
                current=current,
                summary_accepted=summary_accepted,
            )
            end_time = time.time()
            processing_time = end_time - start_time
            print(f"processing_time: {processing_time}")

            input_usage_str = f"{question}\n{baseline}\n{current}"

            output_usage_str = (
                f"{score_data.get('score', 0)} + {score_data.get('reason', '')}"
            )
            update_usage(
                input_str=input_usage_str,
                output_str=output_usage_str,
                processing_time=processing_time,
                key_token=key_token,
            )

            return {
                "score": score_data.get("score", 0),
                "reason": score_data.get("reason", ""),
                "message": "Score Calculated Successfully",
            }, 200
        except Exception as e:
            print("Error: ", e)
            return {"error": str(e)}, 500
        
@api.route("/calculate-score-for-queries")
class CalculateScoreForQueries(Resource):
    @api.expect(cal_score_for_queries_model)
    @api.doc(
        description="Calculate scores for multiple queries.",
        params={
            "key-token": {
                "description": "User identification token",
                "in": "header",
                "type": "string",
                "required": True,
            }
        },
    )
    @api.response(200, "Success", response_cal_scores_for_queries)
    @api.response(
        400, "Quota exceeded / Invalid input / Not found", error_response_model
    )
    @api.response(500, "Internal Server Error", error_response_model)
    def post(self):
        """
        Calculate scores for multiple queries.
        - **queries_data**: Object containing the question, baseline, and current text.
        - **summary_accepted** (Optional bool) : If want to discard summaries set to false, default true.
        """
        key_token = request.headers.get("key-token")
        if not key_token:
            return {"error": "Missing key token."}, 400

        data = request.get_json()

        if data is None:
            return {"error": "No queries data found in the request."}, 400

        if "queries_data" not in data:
            return {"error": "Invalid, input parameters missing."}, 400

        queries_data = data.get("queries_data")
        summary_accepted = data.get("summary_accepted", True)

        try:
            input_usage_str = get_input_str_for_queries(queries_data)
            is_under_limit = check_token_limit(
                input_usage_str=input_usage_str,
                key_token=key_token,
            )
        except ValueError as e:
            return {"error": str(e)}, 400

        if not is_under_limit:
            return {
                "error": "You have used the max number of tokens allowed this month. Please try again later."
            }, 400

        if queue_manager.get_total_queues() > 1:
            return {"error": "Queue Full"}, 400

        try:
            queue_manager.create_and_insert_queries(
                queries_data, summary_accepted=summary_accepted
            )

            start_time = time.time()
            scores_data = get_scores_for_queries(
                queries_data=queries_data, queue_manager=queue_manager
            )
            end_time = time.time()
            processing_time = end_time - start_time
            print(f"processing_time: {processing_time}")

            output_usage_str = get_output_str_for_queries(scores_data)

            update_usage(
                input_str=input_usage_str,
                output_str=output_usage_str,
                processing_time=processing_time,
                avg_queue_time=scores_data["avg_queue_time"],
                key_token=key_token,
            )
            return {"scores": scores_data.get("scores")}
        except Exception as e:
            print("Error in /calculate-score-for-queries route", e)
            return {"error": str(e)}, 500

@judge_ns.route("/compare-qna-sets")
class CompareQnASets(Resource):
    @api.expect(compare_qa_sets_model)
    @api.doc(
        description="Compare two QA sets for a user.",
        params={
            "key-token": {
                "description": "User identification token",
                "in": "header",
                "type": "string",
                "required": True,
            }
        },
    )
    @api.response(200, "Success", response_compare_qa_sets_model)
    @api.response(400, "Invalid input / Not found", error_response_model)
    @api.response(500, "Internal Server Error", error_response_model)
    def post(self):
        """
        Compare two QA sets for a user.
        - **current_set_id**: ID of the current QA set
        - **baseline_set_id**: (optional) ID of the baseline QA set
        - **project_id**: ID of the project
        """
        key_token = request.headers.get("key-token")
        if not key_token:
            return {"error": "Missing key token."}, 400

        # Get JSON data from the request
        data = request.get_json()

        # Input parameter validation
        if not data or ("current_set_id" not in data and "project_id" not in data):
            return {"error": "Invalid input, required parameter is missing"}, 400

        project_id = data["project_id"]
        current_set_id = data["current_set_id"]
        baseline_set_id = data.get("baseline_set_id", None)

        try:
            result = compare_qa_sets(
                key_token=key_token,
                current_set_id=current_set_id,
                baseline_set_id=baseline_set_id,
                project_identifier=project_id,
            )
        except Exception as e:
            print("Error in /compare-qa-sets:", e)
            return {"error": f"{str(e)}"}, 400

        return {
            "response": result,
            "message": "Scores calculated for the current set.",
        }, 200

@judge_ns.route("/get-usage-details")
class GetUsageDetails(Resource):
    @api.doc(
        description="Get usage details for a given email and project ID.",
        params={
            "key-token": {
                "description": "User identification token",
                "in": "header",
                "type": "string",
                "required": True,
            }
        },
    )
    @api.response(200, "Success", output_get_usage_model)
    @api.response(400, "Invalid input / Not found", error_response_model)
    @api.response(500, "Internal Server Error", error_response_model)
    def get(self):
        """
        Get usage details for a given user.
        """
        key_token = request.headers.get("key-token")
        if not key_token:
            return {"error": "Missing key token."}, 400

        try:
            # Call your function to fetch usage details (the result would be dynamic based on the DB)
            result = get_usage_details(key_token=key_token)
        except Exception as e:
            print("Error in /get-usage-details:", e)
            return {"error": f"{str(e)}"}, 500

        return {
            "response": result,
            "message": "Usage details retrieved.",
        }, 200

@judge_ns.route("/retrieve-answer-from-rag")
class RetrieveAnswersFromRag(Resource):
    @api.expect(input_get_answer_from_rag, validate=True)  # Validates the input payload
    @api.doc(
        description="Retrieve answers from user's rag.",
        params={
            "key-token": {
                "description": "User identification token",
                "in": "header",
                "type": "string",
                "required": True,
            }
        },
    )
    @api.response(200, "Success", response_get_answer_from_rag_model)
    @api.response(400, "Invalid input / Not found", error_response_model)
    @api.response(500, "Internal Server Error", error_response_model)
    def post(self):
        """
        Retrieve answers from user's rag.
        **base_url (str)**: Base URL of the user application/api
        **questions (dict)**: A dictionary of questions with IDs as keys
        """
        key_token = request.headers.get("key-token")
        if not key_token:
            return {"error": "Missing key token."}, 400

        # Get JSON data from the request
        data = request.get_json()

        # Validate input parameters
        if "base_url" not in data or "questions" not in data:
            return {"error": "Invalid input, required parameter is missing"}, 400

        base_url = data["base_url"]
        questions = data["questions"]

        try:
            # Call the get_score_from_rag function to get the answers
            result = get_score_from_rag(base_url=base_url, questions=questions)
        except Exception as e:
            print("Error: ", e)
            return {"error": "Internal server error."}, 500

        # Return the answers
        return {"answer": result}, 200

@judge_ns.route("/get-set-ids")
class GetSetIds(Resource):
    @api.response(200, "Success", output_get_set_ids_model)
    @api.response(400, "Invalid input / Not found", error_response_model)
    @api.response(500, "Internal Server Error", error_response_model)
    @api.doc(
        description="Get set ids for user.",
        params={
            "key-token": {
                "description": "User identification token",
                "in": "header",
                "type": "string",
                "required": True,
            },
            "project_id": {
                "description": "Project ID",
                "in": "query",
                "type": "integer",
                "required": True,
            },
        },
    )
    def get(self):
        """
        Get set ids for user.
        """
        key_token = request.headers.get("key-token")
        if not key_token:
            return {"error": "Missing key token."}, 400

        project_id = request.args.get("project_id")
        if not project_id:
            return {"error": "Missing project id."}, 400

        try:
            # Call your function to fetch usage details (the result would be dynamic based on the DB)
            result = get_set_ids(key_token=key_token, project_identifier=project_id)
        except Exception as e:
            print("Error in /get-set-ids:", e)
            return {"error": f"{str(e)}"}, 00

        return {
            "response": result,
            "message": "Set IDs retreived",
        }, 200

@judge_ns.route("/get-project-ids")
class GetProjectIds(Resource):
    @api.response(200, "Success", output_get_project_ids_model)
    @api.response(400, "Invalid input / Not found", error_response_model)
    @api.response(500, "Internal Server Error", error_response_model)
    @api.doc(
        description="Get project ids and there respective data for the user.",
        params={
            "key-token": {
                "description": "User identification token",
                "in": "header",
                "type": "string",
                "required": True,
            }
        },
    )
    def get(self):
        """
        Get project ids and there respective data for the user.
        """
        key_token = request.headers.get("key-token")
        if not key_token:
            return {"error": "Missing key token."}, 400

        try:
            # function to fetch all the projects data
            result = get_project_ids(key_token=key_token)
        except Exception as e:
            print("Error in /get-set-ids:", e)
            return {"error": f"{str(e)}"}, 00

        return {
            "project_data": result,
            "message": "Projects data retreived",
        }, 200


@judge_ns.route("/get-specific-project-details")
class GetSpecificProject(Resource):
    @api.response(200, "Success", output_get_specific_project_model)
    @api.response(400, "Invalid input / Not found", error_response_model)
    @api.response(500, "Internal Server Error", error_response_model)
    @api.doc(
        description="Get specific project and there respective data for the user.",
        params={
            "key-token": {
                "description": "User identification token",
                "in": "header",
                "type": "string",
                "required": True,
            },
            "project_id": {
                "description": "Project ID",
                "in": "query",
                "type": "integer",
                "required": True,
            },
        },
    )
    def get(self):
        """
        Get specific project and there respective data for the user.
        """
        key_token = request.headers.get("key-token")
        if not key_token:
            return {"error": "Missing key token."}, 400

        project_id = request.args.get("project_id")
        if not project_id:
            return {"error": "Missing project id."}, 400
        try:
            # function to fetch all the projects data
            result = get_specific_project_details(
                key_token=key_token, project_identifier=project_id
            )
        except Exception as e:
            print("Error in /get-set-ids:", e)
            return {"error": f"{str(e)}"}, 00

        return {
            "project_data": result,
            "message": "Projects data retreived",
        }, 200

@judge_ns.route("/create-project")
class CreateProject(Resource):
    @api.response(200, "Success", output_create_project_model)
    @api.response(400, "Invalid input / Not found", error_response_model)
    @api.response(500, "Internal Server Error", error_response_model)
    @api.expect(input_create_project_model)
    @api.doc(
        description="Create project for user.",
        params={
            "key-token": {
                "description": "User identification token",
                "in": "header",
                "type": "string",
                "required": True,
            }
        },
    )
    def post(self):
        """
        Create project for user.
        **project_name (str)**: Name of the project
        """
        key_token = request.headers.get("key-token")
        if not key_token:
            return {"error": "Missing key token."}, 400

        data = request.get_json()

        if data is None or "project_name" not in data:
            return {"error": "Invalid input, required parameter is missing"}, 400

        project_name = data["project_name"]

        try:
            # create project against the user.
            result = create_project(key_token=key_token, project_name=project_name)
        except Exception as e:
            print("Error in /create-project:", e)
            return {"error": f"{str(e)}"}, 400

        project_id = list(result.keys())[0]
        return {
            "response": {"project_id": project_id, "project_name": project_name}
        }, 200


@judge_ns.route("/delete-project")
class DeleteProject(Resource):
    @api.response(200, "Success", output_delete_project_model)
    @api.response(400, "Invalid input / Not found", error_response_model)
    @api.response(500, "Internal Server Error", error_response_model)
    @api.doc(
        description="Delete project for user.",
        params={
            "key-token": {
                "description": "User identification token",
                "in": "header",
                "type": "string",
                "required": True,
            },
            "project_id": {
                "description": "Project ID",
                "in": "query",
                "type": "integer",
                "required": True,
            },
        },
    )
    def delete(self):
        """
        Delete project for user.
        """
        key_token = request.headers.get("key-token")
        if not key_token:
            return {"error": "Missing key token."}, 400

        project_id = request.args.get("project_id")
        if not project_id:
            return {"error": "Missing project id."}, 400

        try:
            # Call your function to fetch usage details (the result would be dynamic based on the DB)
            delete_project(key_token=key_token, project_id=project_id)
        except Exception as e:
            print("Error in /delete-project:", e)
            return {"error": f"{str(e)}"}, 500

        return {"message": "Project deleted"}, 200

@judge_ns.route("/update-project-name")
class UpdateProjectName(Resource):
    @api.response(200, "Success", output_update_project_name_model)
    @api.response(400, "Invalid input / Not found", error_response_model)
    @api.response(500, "Internal Server Error", error_response_model)
    @api.doc(
        description="Update project name for user.",
        params={
            "key-token": {
                "description": "User identification token",
                "in": "header",
                "type": "string",
                "required": True,
            },
            "project_id": {
                "description": "Project ID",
                "in": "query",
                "type": "integer",
                "required": True,
            },
            "project_name": {
                "description": "Project name",
                "in": "query",
                "type": "string",
                "required": True,
            },
        },
    )
    def put(self):
        """
        Update project name for user.
        """
        key_token = request.headers.get("key-token")
        if not key_token:
            return {"error": "Missing key token."}, 400

        project_id = request.args.get("project_id")
        if not project_id:
            return {"error": "Missing project id."}, 400

        project_name = request.args.get("project_name")
        if not project_name:
            return {"error": "Missing project name."}, 400

        try:
            # Call your function to fetch usage details (the result would be dynamic based on the DB)
            update_project_name(
                key_token=key_token, project_id=project_id, project_name=project_name
            )
        except Exception as e:
            print("Error in /update-project-name:", e)
            return {"error": f"{str(e)}"}, 500

        return {"message": "Project name updated to " + project_name}


@judge_ns.route("/delete-qa-set")
class DeleteQaSet(Resource):
    @api.response(200, "Success", output_delete_qa_set_model)
    @api.response(400, "Invalid input / Not found", error_response_model)
    @api.response(500, "Internal Server Error", error_response_model)
    @api.doc(
        description="Delete QA set for user.",
        params={
            "key-token": {
                "description": "User identification token",
                "in": "header",
                "type": "string",
                "required": True,
            },
            "set_id": {
                "description": "QA set ID",
                "in": "query",
                "type": "integer",
                "required": True,
            },
            "project_id": {
                "description": "Project ID",
                "in": "query",
                "type": "integer",
                "required": True,
            },
        },
    )
    def delete(self):
        """
        Delete QA set for user.
        """
        key_token = request.headers.get("key-token")
        if not key_token:
            return {"error": "Missing key token."}, 400

        set_id = request.args.get("set_id")
        if not set_id:
            return {"error": "Missing set id."}, 400
        
        project_id = request.args.get("project_id")
        if not project_id:
            return {"error": "Missing project id."}, 400

        try:
            set_id = int(set_id)
        except ValueError:
            return {"error": "Invalid set id."}, 400

        try:
            delete_qa_set(key_token=key_token, set_id=set_id, project_identifier=project_id)
        except Exception as e:
            print("Error in /delete-qa-set:", e)
            return {"error": f"{str(e)}"}, 400

        return {"message": "QA set deleted"}, 200
