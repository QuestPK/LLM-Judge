from flask import Blueprint, render_template, jsonify, request
from flasgger import Swagger
from .utils import get_score_data

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

    baseline = data.get("baseline", "")
    current = data.get("current", "")
    summary_accepted = data.get("summary_accepted", False)

    if not baseline or not current:
        return jsonify({'error': 'Baseline or Current missing.'}), 400
    
    try:
        score_data = get_score_data(
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




