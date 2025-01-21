import uuid
from pprint import pprint

from flask import Blueprint, render_template, jsonify, request
from flasgger import Swagger

from .judge_utilities import get_score_data, get_scores_for_queries
from .db_utils import (
    update_key_token, 
    update_usage,
    check_token_limit,
    get_input_str_for_queries,
    get_output_str_for_queries,
    add_qa,
    update_baseline,
    update_qa
)
from .queues import queue_manager


main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return "Hi, home page!"

@main_bp.route('/get-score', methods=['POST'])
def get_score() -> dict:
    """
    Example API Input/Output:

    Input:
    {
        "question": "question string",
        "baseline": "baseline string",
        "current": "current string",
        "summary_accepted": true
    }

    Successful Response:
    {
        "response": "Scoring Result",
        "reason": "Reason for score",
        "message": "Score Calculated Successfully"
    }

    Error Response:
    {
        "error": "Error message detailing what went wrong"
    }
    """
    data = request.get_json()

    if data is None:
        return jsonify({'error': 'No valid JSON data found in the request.'}), 400

    if "query_data" not in data and \
        "email" not in data:
        return jsonify({'error': 'Invalid, input parameters missing.'}), 400
    
    query_data = data.get("query_data")
    email = data.get("email", "")

    question = query_data.get("question", "")
    baseline = query_data.get("baseline", "")
    current = query_data.get("current", "")
    summary_accepted = data.get("summary_accepted", False)

    if not baseline or not current or not question:
        return jsonify({'error': 'Baseline or Current missing.'}), 400
    
    try:
        input_usage_str = f"{question}\n{baseline}\n{current}"

        is_under_limit = check_token_limit(input_usage_str, email)

        if not is_under_limit:
            return jsonify({
                "error": "You have used the max number of tokens allowed this month. Please try again later."
            })
        score_data = get_score_data(
            question=question,
            baseline=baseline,
            current=current,
            summary_accepted=summary_accepted
        )

        print("\nOutput: ", score_data)

        output_usage_str = f"{score_data.get('score', 0)} + {score_data.get('reason', '')}" 
        update_usage(
            input_str=input_usage_str,
            output_str=output_usage_str,
            email=email
        )
        return jsonify({
            "response": score_data.get("score", 0),
            "reason": score_data.get("reason", ""),
            "message": "Score Calculated Successfully"
        })
    except Exception as e:
        print("Error in /get-score route:", e)
        return jsonify({'error': str(e)}), 500

@main_bp.route('/get-score-for-queries', methods=['POST'])
def get_score_for_queries() -> dict:
    """
    Example API Input/Output:

    Input:
    {"queries_data" : [
            {"query_id" : {
                    "question": "question string",
                    "baseline": "baseline string",
                    "current": "current string",
                    "summary_accepted": true
                },
            },
            ...
        ]
    }

    Successful Response:
    {"queries_data" : [
            {query_id : {
                    "response": "Scoring Result",
                    "reason": "Reason for score",
                    "message": "Score Calculated Successfully"
                }, ...
            }, 
            ...
        ]
    }

    Error Response:
    {
        "error": "Error message detailing what went wrong"
    }
    """
    data = request.get_json()

    if data is None:
        return jsonify({'error': 'No queries data found in the request.'}), 400
    
    if "queries_data" not in data and \
        "email" not in data:
        return jsonify({'error': 'Invalid, input parameters missing.'}), 400
    
    email = data.get("email", "")
    queries_data = data.get("queries_data")

    input_usage_str = get_input_str_for_queries(queries_data)
    is_under_limit = check_token_limit(input_usage_str, email)

    if not is_under_limit:
        return jsonify({
            "error": "You have used the max number of tokens allowed this month. Please try again later."
        })
    
    print("Total Queues: ", queue_manager.get_total_queues(), end='\n')
    if queue_manager.get_total_queues() > 1:
        return jsonify({
            "error" : "Queue Full"
        })
    
    try:
        # pprint(queries_data)

        queue_manager.create_and_insert_queries(queries_data)

        queue_manager.display_all_items()

        scores_data = get_scores_for_queries(
            queries_list=queries_data,
            queue_manager=queue_manager
        )
        
        print("\nScores data")
        pprint(scores_data)

        output_usage_str = get_output_str_for_queries(scores_data)
        update_usage(
            input_str=input_usage_str,
            output_str=output_usage_str,
            email=email
        )

        return jsonify({
            # "scores_data": scores_data
            "scores_data": scores_data
        })
    except Exception as e:
        print("Error in /get-score-for-queries route:", e)
        return jsonify({'error': "Error in /get-score-for-queries route"}), 500

@main_bp.route("/get-key-token", methods=["POST"])
def get_key_token():
    # Get JSON data from the request
    data = request.json

    # Validate input
    if not data or "email" not in data:
        return jsonify({"error": "Invalid input, 'email' key is required"}), 400

    email = data["email"]

    # Find and update the document if it exists, or insert a new one
    result, new_key_token = update_key_token(email)

    # Determine the operation performed
    if result.matched_count > 0:
        message = "Email found. key_token updated."
    else:
        message = "Email not found. New document added."

    return jsonify({
        "message": message,
        "email": email,
        "key_token": new_key_token,
    }), 200

@main_bp.route("/set-qa", methods=["POST"])
def set_qa():
    # Get JSON data from the request
    data = request.json

    # input parameter validation
    if not data or \
        "email" not in data or \
            "qa_data" not in data:
        return jsonify({"error": "Invalid input, required parameter is missing"}), 400

    email = data["email"]
    qa = data["qa_data"]

    try:
        add_qa(email, qa)
    except Exception as e:
        print("Error in /set-qa route:", e)
        return jsonify({'error': "Error in /set-qa: " + str(e)}), 400
    
    return jsonify({
        "response": "QA set added against: set_id: {}, email: {}".format(qa["set_id"], email)
    }), 200

@main_bp.route("/set-baseline", methods=["POST"])
def set_baseline():
    # Get JSON data from the request
    data = request.json

    # input parameter validation
    if not data or \
        "email" not in data or \
            "set_id" not in data:
        return jsonify({"error": "Invalid input, required parameter is missing"}), 400

    email = data["email"]
    set_id = data["set_id"]

    try:
        update_baseline(email, set_id)
    except Exception as e:
        print("Error in /set-baseline route:", e)
        return jsonify({'error': "Error in /set-baseline: " + str(e)}), 400
    
    return jsonify({
        "response": "Baseline updated added against: set_id: {}, email: {}".format(set_id, email)
    }), 200

@main_bp.route("/update-qa", methods=["POST"])
def update_qa_view():
    # Get JSON data from the request
    data = request.json

    # input parameter validation
    if not data or \
        "email" not in data or \
            "qa_data" not in data:
        return jsonify({"error": "Invalid input, required parameter is missing"}), 400

    email = data["email"]
    qa = data["qa_data"]

    try:
        update_qa(email, qa)
    except Exception as e:
        print("Error in /update-qa route:", e)
        return jsonify({'error': "Error in /update-qa: " + str(e)}), 400
    
    return jsonify({
        "response": "QA set updated against: set_id: {}, email: {}".format(qa["set_id"], email)
    }), 200
