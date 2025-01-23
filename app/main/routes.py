import uuid
from pprint import pprint

from flask import Blueprint, render_template, jsonify, request
from flask_restx import Api, Resource, fields

from .judge_utilities import get_score_data, get_scores_for_queries
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
)
from .queues import queue_manager

main_bp = Blueprint("main", __name__)

# Api instance for Swagger documentation
api = Api(
    main_bp,
    version="1.0",
    title="Judge API's Testing",
    description="API's for testing",
    doc="/api-docs",
)

get_score_model = api.model(
    "GetScore",
    {
        "query_data": fields.Nested(
            api.model(
                "QueryData",
                {
                    "question": fields.String(
                        required=True, description="The question string", example="What is capital of france?"
                    ),
                    "baseline": fields.String(
                        required=True, description="The baseline string", example="Paris"
                    ),
                    "current": fields.String(
                        required=True, description="The current string", example="I don't know"
                    ),
                },
            )
        ),
        "email": fields.String(required=True, description="User email", example="umertest123@gmail.com"),
        "summary_accepted": fields.Boolean(
            required=False, description="Whether the summary is accepted", example=True
        ),
    },
)
@api.route("/get-score")
class GetScore(Resource):
    @api.expect(get_score_model)
    @api.doc(
        description="Calculate the score for a given question, baseline, and current text."
    )
    @api.response(200, "Success")
    @api.response(400, "Quota exceeded / Invalid input / Not found")
    @api.response(500, "Internal Server Error")
    def post(self):
        """
        Calculate the score for a given question, baseline, and current text.
        - **query_data**: Object containing the question, baseline, and current text.
        - **email**: User's email address.
        - **summary_accepted**: Whether the summary is accepted or not.
        """
        data = request.get_json()

        if data is None:
            return {"error": "No valid JSON data found in the request."}, 400

        if "query_data" not in data or "email" not in data:
            return {"error": "Invalid, input parameters missing."}, 400

        query_data = data.get("query_data")
        email = data.get("email", "")

        question = query_data.get("question", "")
        baseline = query_data.get("baseline", "")
        current = query_data.get("current", "")
        summary_accepted = data.get("summary_accepted", False)

        if not baseline or not current or not question:
            return {"error": "Baseline or Current missing."}, 400

        try:
            input_usage_str = f"{question}\n{baseline}\n{current}"
            is_under_limit = check_token_limit(input_usage_str, email)

            if not is_under_limit:
                return {
                    "error": "You have used the max number of tokens allowed this month. Please try again later."
                }, 400  # Ensure you return the appropriate error code here.

            score_data = get_score_data(
                question=question,
                baseline=baseline,
                current=current,
                summary_accepted=summary_accepted,
            )

            return {
                "response": score_data.get("score", 0),
                "reason": score_data.get("reason", ""),
                "message": "Score Calculated Successfully",
            }, 200
        except Exception as e:
            return {"error": str(e)}, 500


get_score_for_queries_model = api.model(
    "GetScoreForQueries",
    {
        "queries_data": fields.List(
            fields.Nested(
                api.model(
                    "QueryItem",
                    {
                        "query_id": fields.Nested(
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
                            ), example={"question": "What is capital of france?", "baseline": "Paris", "current": "I don't know"}
                        ),
                    },
                )
            )
        ),
        "email": fields.String(required=True, description="User email", example="umertest123@gmail.com"),
    },
)
@api.route("/get-score-for-queries")
class GetScoreForQueries(Resource):
    @api.expect(get_score_for_queries_model)
    @api.doc(description="Calculate scores for multiple queries.")
    @api.response(200, "Success")
    @api.response(400, "Quota exceeded / Invalid input / Not found")
    @api.response(500, "Internal Server Error")
    def post(self):
        """
        Calculate scores for multiple queries.
        - **queries_data**: List of query objects containing question, baseline, and current text.
        - **email**: User's email address.
        """
        data = request.get_json()

        if data is None:
            return {"error": "No queries data found in the request."}, 400

        if "queries_data" not in data and "email" not in data:
            return {"error": "Invalid, input parameters missing."}, 400

        email = data.get("email", "")
        queries_data = data.get("queries_data")

        input_usage_str = get_input_str_for_queries(queries_data)
        is_under_limit = check_token_limit(input_usage_str, email)

        if not is_under_limit:
            return {
                "error": "You have used the max number of tokens allowed this month. Please try again later."
            }

        if queue_manager.get_total_queues() > 1:
            return {"error": "Queue Full"}

        try:
            queue_manager.create_and_insert_queries(queries_data)
            scores_data = get_scores_for_queries(
                queries_list=queries_data, queue_manager=queue_manager
            )

            return {"scores_data": scores_data}
        except Exception as e:
            return {"error": "Error in /get-score-for-queries route"}, 500


get_key_token_model = api.model(
    "GetKeyToken", 
    {
        "email": fields.String(required=True, description="User email", example="umertest123@gmail.com"),
    }
)
@api.route("/get-key-token")
class GetKeyToken(Resource):
    @api.expect(get_key_token_model)
    @api.doc(description="Retrieve or create a unique key token for a given email.")
    @api.response(200, "Success")
    @api.response(400, "Quota exceeded / Invalid input / Not found")
    @api.response(500, "Internal Server Error")
    def post(self):
        """
        Retrieve or create a unique key token for a given email.
        - **email**: User's email address.
        """
        data = request.json

        if not data or "email" not in data:
            return {"error": "Invalid input, 'email' key is required"}, 400

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
            "email": email,
            "key_token": new_key_token,
        }, 200


set_qa_request_model = api.model(
    "Set QA",
    {
        "email": fields.String(
            required=True,
            description="Email address of the user",
            example="umertest123@gmail.com",
        ),
        "project_id": fields.Integer(
            required=True,
            description="Project ID",
            example=22,
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
                    }
                ],
                "set_id": 78,
            },
        ),
    },
)
# Route for adding a new QA set
@api.route("/set-qa")
class SetQA(Resource):
    @api.expect(set_qa_request_model)
    @api.doc(description="Add a new QA set for a given email.")
    @api.response(200, "Success")
    @api.response(400, "Invalid input / Not found")
    @api.response(500, "Internal Server Error")
    def post(self):
        """
        Adds a new QA set for the given email.

        - **email**: Email address of the user
        - **project_id**: Project ID
        - **qa_data**: QA data object with set_id
        """
        data = request.json
        if (
            not data
            or "project_id" not in data
            or "email" not in data
            or "qa_data" not in data
        ):
            return {"error": "Invalid input, required parameter is missing"}, 400

        email = data["email"]
        project_id = data["project_id"]
        qa_data = data["qa_data"]

        try:
            # Simulated logic for adding QA
            add_qa(email=email, project_id=project_id, qa_data=qa_data)
            return {
                "response": f"QA set added against: set_id: {qa_data['set_id']}, email: {email}"
            }, 200
        except Exception as e:
            return {"error": f"Error in /set-qa: {str(e)}"}, 400


baseline_model = api.model(
    "Baseline",
    {
        "email": fields.String(
            required=True,
            description="Email address of the user",
            example="umertest123@gmail.com",
        ),
        "set_id": fields.Integer(
            required=True, description="QA set ID", example=786
        ),
        "project_id": fields.Integer(
            required=True, description="Project ID", example=22
        ),
    },
)
# Route for setting a baseline
@api.route("/set-baseline")
class SetBaseline(Resource):
    @api.expect(baseline_model)
    @api.doc(
        description="Set provided set as a baseline for a given email and project id."
    )
    @api.response(200, "Success")
    @api.response(400, "Invalid input / Not found")
    @api.response(500, "Internal Server Error")
    def post(self):
        """
        Sets a baseline for the given email and set ID.

        - **email**: Email address of the user
        - **set_id**: QA set ID
        - **project_id**: Project ID
        """
        data = request.json
        if (
            not data
            or "email" not in data
            or "project_id" not in data
            or "set_id" not in data
        ):
            return {"error": "Invalid input, required parameter is missing"}, 400

        email = data["email"]
        set_id = data["set_id"]
        project_id = data["project_id"]

        try:
            # Simulated logic for setting baseline
            update_baseline(email=email, project_id=project_id, set_id=set_id)
            return {
                "response": f"Baseline updated against: set_id: {set_id}, email: {email}"
            }, 200
        except Exception as e:
            return {"error": f"Error in /set-baseline: {str(e)}"}, 400


# Model for updating QA
update_qa_model = api.model(
    "UPdate QA Request",
    {
        "email": fields.String(
            required=True,
            description="Email address of the user",
            example="umertest123@gmail.com",
        ),
        "project_id": fields.Integer(
            required=True,
            description="Project ID",
            example=22,
        ),
        "qa_data": fields.Raw(
            required=True,
            description="QA data to be updated (generic structure)",
            example={
                "qa_set": [
                    {
                        "id": 1,
                        "question": "what is the capital of france?",
                        "answer": "Paris",
                    }
                ],
                "set_id": 78,
            },
        ),
    },
)
@api.route("/update-qa")
class UpdateQA(Resource):
    @api.expect(update_qa_model)
    def post(self):
        """
        Update an existing QA set for a given email.

        - **email**: Email address of the user
        - **project_id**: Project ID
        - **qa_data**: QA data object with set_id
        """
        # Get JSON data from the request
        data = request.json

        # Input parameter validation
        if (
            not data
            or "email" not in data
            or "project_id" not in data
            or "qa_data" not in data
        ):
            return {"error": "Invalid input, required parameter is missing"}, 400

        email = data["email"]
        qa = data["qa_data"]
        project_id = data["project_id"]

        try:
            # Attempt to update the QA set
            update_qa(email=email, project_id=project_id, qa_data=qa)
        except Exception as e:
            print("Error in /update-qa route:", e)
            return {"error": f"Error in /update-qa: {str(e)}"}, 400

        return {
            "response": f"QA set updated against: set_id: {qa['set_id']}, email: {email}"
        }, 200


# Model for comparing QA sets
compare_qa_sets_model = api.model(
    "CompareQASets",
    {
        "email": fields.String(
            required=True, description="The email address of the user", example="umertest123@gmail.com"
        ),
        "project_id": fields.Integer(
            required=True, description="The ID of the project", example=22
        ),
        "current_set_id": fields.Integer(
            required=True, description="The ID of the current QA set", example=786
        ),
        "baseline_set_id": fields.Integer(
            description="The ID of the baseline QA set (optional)", example=786,
            required=False,
        ),
    },
)
@api.route("/compare-qa-sets")
class CompareQASets(Resource):
    @api.expect(compare_qa_sets_model)
    @api.doc(description="Compare two QA sets for a given email and project ID.")
    @api.response(200, "Success")
    @api.response(400, "Invalid input / Not found")
    @api.response(500, "Internal Server Error")
    def post(self):
        """
        Compare two QA sets for a given email and project ID.
        - **email**: Email address of the user
        - **project_id**: Project ID
        - **current_set_id**: ID of the current QA set
        - **baseline_set_id**: (optional) ID of the baseline QA set
        """
        # Get JSON data from the request
        data = request.json

        # Input parameter validation
        if (
            not data
            or "email" not in data
            or "project_id" not in data
            or "current_set_id" not in data
        ):
            return {"error": "Invalid input, required parameter is missing"}, 400

        email = data["email"]
        project_id = data["project_id"]
        current_set_id = data["current_set_id"]
        baseline_set_id = data.get("baseline_set_id", None)

        try:
            result = compare_qa_sets(
                email=email,
                project_id=project_id,
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
