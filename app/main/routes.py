import uuid
from pprint import pprint
import time

from flask import Blueprint, render_template, jsonify, request
from flask_restx import Api, Resource, fields

from .judge_utilities import get_score_data, get_scores_for_queries, get_score_from_rag
from .db_utils import (
    update_key_token,
    update_usage,
    check_token_limit,
    get_input_str_for_queries,
    get_output_str_for_queries,
    add_qa,
    update_baseline,
    update_qa,
    compare_qa_sets,
    get_usage_details,
)
from .queues import queue_manager

main_bp = Blueprint("main", __name__)

# Api instance for Swagger documentation
api = Api(
    main_bp,
    version="1.1",
    title="Judge API's Testing",
    description="API's for testing",
    doc="/api-docs",
)

# input /get-score
get_score_model = api.model(
    "GetScore",
    {
        "query_data": fields.Nested(
            api.model(
                "QueryData",
                {
                    "question": fields.String(
                        required=True,
                        description="The question string",
                        example="What is capital of france?",
                    ),
                    "baseline": fields.String(
                        required=True,
                        description="The baseline string",
                        example="Paris",
                    ),
                    "current": fields.String(
                        required=True,
                        description="The current string",
                        example="I don't know",
                    ),
                },
            )
        ),
        "key_token": fields.String(
            required=True, description="User key token", example="12345abcdef67890"
        ),
        "summary_accepted": fields.Boolean(
            required=False, description="Whether the summary is accepted", example=True
        ),
    },
)

# output model
output_get_score_model = api.model(
    "OutputGetScore",
    {
        "score": fields.Raw(
            {
                "score": "Integer Score",
                "reason": "Reason of score",
                "message": "API message",
            }
        ),
    },
)
# model for error responses
error_response_model = api.model(
    "ErrorResponse",
    {
        "error": fields.String(description="Error message", example="Error details."),
    },
)


@api.route("/get-score")
class GetScore(Resource):
    @api.expect(get_score_model)
    @api.doc(
        description="Calculate the score for a given question, baseline, and current text."
    )
    @api.response(200, "Success", output_get_score_model)
    @api.response(
        400, "Quota exceeded / Invalid input / Not found", error_response_model
    )
    @api.response(500, "Internal Server Error", error_response_model)
    def post(self):
        """
        Calculate the score for a given question, baseline, and current text.
        - **query_data**: Object containing the question, baseline, and current text.
        - **key_token**: User identifier.
        - **summary_accepted**: Whether the summary is accepted or not.
        """
        data = request.get_json()

        if data is None:
            return {"error": "No valid JSON data found in the request."}, 400

        if "query_data" not in data or "key_token" not in data :
            return {"error": "Invalid, input parameters missing."}, 400

        query_data = data.get("query_data")
        key_token = data.get("key_token", "")

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
                    input_usage_str=input_usage_str, 
                    key_token=key_token
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
                key_token=key_token
            )

            return {
                "score": score_data.get("score", 0),
                "reason": score_data.get("reason", ""),
                "message": "Score Calculated Successfully",
            }, 200
        except Exception as e:
            print("Error: ", e)
            return {"error": str(e)}, 500


# input /get-scores-for-queries
get_score_for_queries_model = api.model(
    "GetScoreForQueries",
    {
        "queries_data": fields.List(
            fields.Nested(
                api.model(
                    "QueryItem",
                    {
                        "123": fields.Nested(
                            api.model(
                                "QueryDetails",
                                {
                                    "question": fields.String(
                                        required=True, description="The question string"
                                    ),
                                    "baseline": fields.String(
                                        required=True, description="The baseline string"
                                    ),
                                    "current": fields.String(
                                        required=True, description="The current string"
                                    )
                                },
                            ),
                            example={
                                "question": "What is capital of france?",
                                "baseline": "Paris",
                                "current": "I don't know",
                            },
                        ),
                        "456": fields.Nested(
                            api.model(
                                "QueryDetails",
                                {
                                    "question": fields.String(
                                        required=True, description="The question string"
                                    ),
                                    "baseline": fields.String(
                                        required=True, description="The baseline string"
                                    ),
                                    "current": fields.String(
                                        required=True, description="The current string"
                                    ),
                                },
                            ),
                            example={
                                "question": "What is capital of Pakistan?",
                                "baseline": "Islamabad",
                                "current": "Islamabad",
                            },
                        ),
                    },
                )
            )
        ),
        "key_token": fields.String(
            required=True, description="User key token", example="12345abcdef67890"
        ),
    },
)
# output /get-scores-for-queries
response_get_scores_for_queries = api.model(
    "ScoresContainer",
    {
        "scores": fields.Raw(
            required=True,
            description="A dictionary containing score objects indexed by IDs",
            example={
                "12": {
                    "score": 1,
                    "reason": "The response is completely not relevant and does not provide the correct information.",
                },
                "34": {
                    "score": 1,
                    "reason": "The response is completely irrelevant and does not provide any correct information.",
                },
            },
        )
    },
)


@api.route("/get-score-for-queries")
class GetScoreForQueries(Resource):
    @api.expect(get_score_for_queries_model)
    @api.doc(description="Calculate scores for multiple queries.")
    @api.response(200, "Success", response_get_scores_for_queries)
    @api.response(
        400, "Quota exceeded / Invalid input / Not found", error_response_model
    )
    @api.response(500, "Internal Server Error", error_response_model)
    def post(self):
        """
        Calculate scores for multiple queries.
        - **key_token**: User identifier.
        - **query_data**: Object containing the question, baseline, and current text.
        """
        data = request.get_json()

        if data is None:
            return {"error": "No queries data found in the request."}, 400

        if "queries_data" not in data and "key_token" not in data:
            return {"error": "Invalid, input parameters missing."}, 400

        key_token = data.get("key_token", "")
        queries_data = data.get("queries_data")

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
            queue_manager.create_and_insert_queries(queries_data)

            start_time = time.time()
            scores_data = get_scores_for_queries(
                queries_list=queries_data, queue_manager=queue_manager
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
            return {"error": "Error in /get-score-for-queries route"}, 500


# Input model for /get-key-token
input_get_key_token_model = api.model(
    "GetKeyToken",
    {
        "email": fields.String(
            required=True, description="User email", example="test123@gmail.com"
        )
    },
)
# response models
output_get_key_token_model = api.model(
    "OutputGetKeyToken",
    {
        "message": fields.String(
            description="Success message", example="Email found. key_token updated."
        ),
        "key_token": fields.String(
            description="Generated key token", example="12345-abcdef-67890"
        ),
    },
)


@api.route("/get-key-token")
class GetKeyToken(Resource):
    @api.expect(input_get_key_token_model)
    @api.doc(description="Retrieve and create a unique key token for a given email.")
    @api.response(200, "Success", output_get_key_token_model)
    @api.response(
        400, "Quota exceeded / Invalid input / Not found", error_response_model
    )
    @api.response(500, "Internal Server Error", error_response_model)
    def post(self):
        """
        Retrieve and create a unique key token for a given email. It will create a new data document if the email and project ID are not found.
        - **email**: User's email address.
        """
        data = request.json

        if not data or "email" not in data:
            return {
                "error": "Invalid input, 'email' key is required"
            }, 400

        email = data["email"]
    
        result, new_key_token = update_key_token(email)

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


input_set_qa_request_model = api.model(
    "Set QnA",
    {
        "key_token": fields.String(
            required=True,
            description="User Identifier",
            example="12345abcdef67890",
        ),
        "qa_data": fields.Raw(
            required=True,
            description="QA data to be added (generic structure)",
            example={
                "qa_set": [
                    {
                        "id": 1,
                        "question": "What is the capital of france?",
                        "answer": "Paris",
                    },
                    {
                        "id": 2,
                        "question": "What is the capital of Pakistan?",
                        "answer": "Pakistan",
                    }
                ],
                "set_id": 78,
            },
        ),
    },
)

set_qna_output_model = api.model(
    "Set QnA Output",
    {
        "response": fields.String(
            description="Success message", example="QA set added successfully."
        ),
    },
)


# Route for adding a new QA set
@api.route("/set-qna")
class SetQnA(Resource):
    @api.expect(input_set_qa_request_model)
    @api.doc(description="Add a new QA set for a given email.")
    @api.response(200, "Success", set_qna_output_model)
    @api.response(400, "Invalid input / Not found", error_response_model)
    @api.response(500, "Internal Server Error", error_response_model)
    def post(self):
        """
        Adds a new QA set for the given email.

        - **key_token**: User identifier.
        - **qa_data**: QA data object with set_id
        """
        data = request.json
        if (
            not data
            or "key_token" not in data
            or "qa_data" not in data
        ):
            return {"error": "Invalid input, required parameter is missing"}, 400

        key_token = data["key_token"]
        qa_data = data["qa_data"]

        try:
            # adding QA to db
            add_qa(key_token=key_token, qa_data=qa_data)
            return {
                "response": f"QA set added against: {key_token} successfully."
            }, 200
        except Exception as e:
            return {"error": f"Error in /set-qa: {str(e)}"}, 400


# model for baseline input data
input_set_baseline_model = api.model(
    "Baseline",
    {
        "key_token": fields.String(
            required=True,
            description="user identifier",
            example="12345abcdef67890",
        ),
        "set_id": fields.Integer(required=True, description="QA set ID", example=786),
    },
)
# model for success responses
success_response_model = api.model(
    "SuccessResponse",
    {
        "response": fields.String(
            description="Success message", example="Baseline updated successfully"
        ),
    },
)


# Route for changing baseline set
@api.route("/set-baseline")
class SetBaseline(Resource):
    @api.expect(input_set_baseline_model)
    @api.doc(
        description="Set provided set as a baseline for a given email and project id."
    )
    @api.response(200, "Success", success_response_model)  # Success response
    @api.response(
        400, "Invalid input / Not found", error_response_model
    )  # Invalid input or not found
    @api.response(500, "Internal Server Error", error_response_model)  # Server error
    def post(self):
        """
        Sets a baseline for the given email and set ID.

        - **key_token**: "user identifier"
        - **set_id**: QA set ID
        """
        data = request.json
        if (
            not data
            or "key_token" not in data
            or "set_id" not in data
        ):
            return {"error": "Invalid input, required parameter is missing"}, 400

        key_token = data["key_token"]
        set_id = data["set_id"]

        try:
            # setting baseline (replace this with your actual logic)
            update_baseline(key_token=key_token, set_id=set_id)
            return {
                "response": f"Baseline updated against: {key_token}"
            }, 200
        except ValueError as e:
            # Assuming a custom exception like ValueError for this case
            return {"error": f"Error: {str(e)}"}, 400
        except Exception as e:
            # Handling any general exceptions
            return {"error": f"Error in /set-baseline: {str(e)}"}, 500


# Model for updating QA
input_update_qa_model = api.model(
    "UPdate QnA Request",
    {
        "key_token": fields.String(
            required=True,
            description="user identifier",
            example="12345abcdef67890",
        ),
        "qa_data": fields.Raw(
            required=True,
            description="QA data to be updated (generic structure)",
            example={
                "qa_set": [
                    {
                        "id": 1,
                        "question": "what is the capital of Afghanistan?",
                        "answer": "kabul",
                    },
                    {
                        "id": 2,
                        "question": "what is the capital of India?",
                        "answer": "Delhi",
                    },

                ],
                "set_id": 78,
            },
        ),
    },
)
success_qa_model = api.model(
    "SuccessResponse",
    {
        "response": fields.String(
            description="Success message", example="QA set updated successfully"
        ),
    },
)


@api.route("/update-qna")
class UpdateQnA(Resource):
    @api.expect(input_update_qa_model)
    @api.doc(description="Update an existing QA set for a given user.")
    @api.response(200, "Success", success_qa_model)
    @api.response(400, "Invalid input / Not found", error_response_model)
    @api.response(500, "Internal Server Error", error_response_model)
    def post(self):
        """
        Update an existing QA set for a given email.

        - **key_token**: User Identifier
        - **qa_data**: QA data object with set_id
        """
        # Get JSON data from the request
        data = request.json

        # Input parameter validation
        if (
            not data
            or "key_token" not in data
            or "qa_data" not in data
        ):
            return {"error": "Invalid input, required parameter is missing"}, 400

        key_token = data["key_token"]
        qa = data["qa_data"]

        try:
            # Attempt to update the QA set
            update_qa(key_token=key_token, qa_data=qa)
        except Exception as e:
            print("Error in /update-qa route:", e)
            return {"error": f"Error in /update-qa: {str(e)}"}, 400

        return {
            "response": f"QA set updated against: {key_token} successfully."
        }, 200


# Input Model for /compare-qa-sets
compare_qa_sets_model = api.model(
    "CompareQnASets",
    {
        "key_token": fields.String(
            required=True,
            description="user identifier",
            example="12345abcdef67890",
        ),
        "current_set_id": fields.Integer(
            required=True, description="The ID of the current QA set", example=786
        ),
        "baseline_set_id": fields.Integer(
            description="The ID of the baseline QA set (optional)",
            example=786,
            required=False,
        ),
    },
)

# Output Model for /compare-qa-sets
response_compare_qa_sets_model = api.model(
    "Data",
    {
        "response": fields.Raw(
            required=True,
            description="Response containing dynamic IDs with their details",
            example={
                12: {
                    "reason": "No reason",
                    "score": 0,
                    "question": "",
                    "baseline": "",
                    "current": "",
                },
                34: {
                    "reason": "No reason",
                    "score": 0,
                    "question": "",
                    "baseline": "",
                    "current": "",
                },
            },
        ),
        "message": fields.String(
            required=True, description="Response message", example="Update successful"
        ),
    },
)


@api.route("/compare-qna-sets")
class CompareQnASets(Resource):
    @api.expect(compare_qa_sets_model)
    @api.doc(description="Compare two QA sets for a user.")
    @api.response(200, "Success", response_compare_qa_sets_model)
    @api.response(400, "Invalid input / Not found", error_response_model)
    @api.response(500, "Internal Server Error", error_response_model)
    def post(self):
        """
        Compare two QA sets for a user.
        - **key_token** : User identifier.
        - **current_set_id**: ID of the current QA set
        - **baseline_set_id**: (optional) ID of the baseline QA set
        """
        # Get JSON data from the request
        data = request.json

        # Input parameter validation
        if (
            not data
            or "key_token" not in data
            or "current_set_id" not in data
        ):
            return {"error": "Invalid input, required parameter is missing"}, 400

        key_token = data["key_token"]
        current_set_id = data["current_set_id"]
        baseline_set_id = data.get("baseline_set_id", None)

        try:
            result = compare_qa_sets(
                key_token=key_token,
                current_set_id=current_set_id,
                baseline_set_id=baseline_set_id,
            )
        except Exception as e:
            print("Error in /compare-qa-sets:", e)
            return {"error": f"Error in /compare-qa-sets: {str(e)}"}, 400

        return {
            "response": result,
            "message": "Scores calculated for the current set.",
        }, 200


# Usage details response defined using fields.Raw
output_get_usage_model = api.model(
    "OutputUsageRaw",
    {
        "response": fields.Raw(
            required=True,
            description="Usage details containing token, processing, and request data",
            example={
                "token_used": 570,
                "avg_input_token": 93,
                "avg_output_token": 192,
                "avg_processing_time": 30.44,
                "avg_queue_time": 30.43,
                "number_of_requests": 2,
                "processing_time": 29.98,
            },
        ),
        "message": fields.String(
            required=True,
            description="Response message",
            example="Usage details retrieved.",
        ),
    },
)


@api.route("/get-usage-details")
class GetUsageDetails(Resource):
    @api.doc(
        description="Get usage details for a given email and project ID.",
        params={
            "key_token": "user identifier (required)"
        },
    )
    @api.response(200, "Success", output_get_usage_model)
    @api.response(400, "Invalid input / Not found", error_response_model)
    @api.response(500, "Internal Server Error", error_response_model)
    def get(self):
        """
        Get usage details for a given user.
        - **key_token**: User identifier.
        """
        # Get query parameters
        key_token = request.args.get("key_token")

        # Input parameter validation
        if not key_token:
            return {"error": "Invalid input, key parameters are required"}, 400

        try:
            # Call your function to fetch usage details (the result would be dynamic based on the DB)
            result = get_usage_details(key_token=key_token)
        except Exception as e:
            print("Error in /get-usage-details:", e)
            return {"error": f"Error in /get-usage-details: {str(e)}"}, 500

        return {
            "response": result,
            "message": "Usage details retrieved.",
        }, 200


# questions format
input_get_answer_from_rag_question_format = api.model(
    "Questions",
    {
        "1": fields.String(description="Question 1", example="What is photosynthesis"),
        "2": fields.String(
            description="Question 2", example="What is the capital of France?"
        ),
    },
)

# input payload mdoel
input_get_answer_from_rag = api.model(
    "InputPayload",
    {
        "base_url": fields.String(
            required=True,
            description="Base URL of the (your)API",
            example="http://127.0.0.1:5000/",
        ),
        "questions": fields.Nested(
            input_get_answer_from_rag_question_format,
            required=True,
            description="A dictionary of questions with IDs as keys",
        ),
    },
)

# Output format model for answers
output_get_answer_from_rag_format = api.model(
    "OutputModel",
    {
        "1": fields.String(description="Answer 1", example="It's answer"),
        "2": fields.String(description="Answer 2", example="It's answer"),
    },
)
# response model
response_get_answer_from_rag_model = api.model(
    "Answer", {"answer": fields.Nested(output_get_answer_from_rag_format)}
)


@api.route("/get-answer-from-rag")
class GetAnswersFromRag(Resource):
    @api.expect(input_get_answer_from_rag, validate=True)  # Validates the input payload
    @api.doc(description="Get answers from user's rag.")
    @api.response(200, "Success", response_get_answer_from_rag_model)
    @api.response(400, "Invalid input / Not found", error_response_model)
    @api.response(500, "Internal Server Error", error_response_model)
    def post(self):
        """
        Get answers from user's rag.

        **Input params**:
            **base_url (str)**: Base URL of the user application/api
            **questions (dict)**: A dictionary of questions with IDs as keys
        """
        # Get JSON data from the request
        data = request.json

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
