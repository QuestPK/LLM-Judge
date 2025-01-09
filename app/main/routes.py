import asyncio
from pprint import pprint

from flask import Blueprint, render_template, jsonify, request
from flasgger import Swagger

from .utils import get_score_data, get_scores_for_queries
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

    question = data.get("question", "")
    baseline = data.get("baseline", "")
    current = data.get("current", "")
    summary_accepted = data.get("summary_accepted", False)

    if not baseline or not current or not question:
        return jsonify({'error': 'Baseline or Current missing.'}), 400
    
    try:
        score_data = get_score_data(
            question=question,
            baseline=baseline,
            current=current,
            summary_accepted=summary_accepted
        )

        print("\nOutput: ", score_data)

        return jsonify({
            "response": score_data.get("score", 0),
            "reason": score_data.get("reason", ""),
            "message": "Score Calculated Successfully"
        })
    except Exception as e:
        print("Error in /get-score route:", e)
        return jsonify({'error': str(e)}), 500

@main_bp.route('/get-score-for-queries', methods=['POST'])
async def get_score_for_queries() -> dict:
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

    queries_data = data.get("queries_data", [])

    print("\n==========================\n")

    if data is None or \
        not queries_data:
        return jsonify({'error': 'No queries data found in the request.'}), 400
    
    print("Total Queues: ", queue_manager.get_total_queues())
    if queue_manager.get_total_queues() > 0:
        return jsonify({
            "error" : "Queue Full"
        })
    
    
    # pprint(queries_data)

    queue_manager.create_and_insert_queries(queries_data)

    queue_manager.display_all_items()

    scores_data = await get_scores_for_queries(
        queries_list=queries_data,
        queue_mananager=queue_manager
    )
    
    print("\nScores data")
    pprint(scores_data)

    return jsonify({
        # "scores_data": scores_data
        "scores_data": "Hi"
    })