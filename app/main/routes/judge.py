import time

from flask import request
from flask_restx import Namespace, Resource

from app.main.swagger_models.judge import (
    error_response_model,
    calculate_score_model, output_score_model,
    cal_score_for_queries_model, response_cal_scores_for_queries,
    input_get_answer_from_rag, response_get_answer_from_rag_model, 
)
from app.main.judge_utilities import (
    get_score_data, 
    get_scores_for_queries, 
    get_score_from_rag
)
from app.main.db_utils import update_usage, check_token_limit
from app.main.utils import get_input_str_for_queries, get_output_str_for_queries
from app.main.queues import queue_manager

judge_ns = Namespace(
    name="Judge",
    description="Judge NS",
    path='/'
)

@judge_ns.route("/calculate-score")
class CalculateScore(Resource):
    @judge_ns.expect(calculate_score_model)
    @judge_ns.doc(
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
    @judge_ns.response(200, "Success", output_score_model)
    @judge_ns.response(
        400, "Quota exceeded / Invalid input / Not found", error_response_model
    )
    @judge_ns.response(500, "Internal Server Error", error_response_model)
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

@judge_ns.route("/calculate-score-for-queries")
class CalculateScoreForQueries(Resource):
    @judge_ns.expect(cal_score_for_queries_model)
    @judge_ns.doc(
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
    @judge_ns.response(200, "Success", response_cal_scores_for_queries)
    @judge_ns.response(
        400, "Quota exceeded / Invalid input / Not found", error_response_model
    )
    @judge_ns.response(500, "Internal Server Error", error_response_model)
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
        
@judge_ns.route("/retrieve-answer-from-rag")
class RetrieveAnswersFromRag(Resource):
    @judge_ns.expect(input_get_answer_from_rag, validate=True)  # Validates the input payload
    @judge_ns.doc(
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
    @judge_ns.response(200, "Success", response_get_answer_from_rag_model)
    @judge_ns.response(400, "Invalid input / Not found", error_response_model)
    @judge_ns.response(500, "Internal Server Error", error_response_model)
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