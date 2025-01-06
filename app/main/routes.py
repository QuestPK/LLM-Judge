from flask import Blueprint, render_template, jsonify, request
from flasgger import Swagger
from .utils import get_response_from_llm

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
        "current": "current string"
    }

    Successful Response:
    {
        "response": "Scoring Result",
        "message": "Score"
    }

    Error Response:
    {
        "error": "Error message detailing what went wrong"
    }

    ### Todo's: 
    ###   1. Summary acceptance
    """
    # Get the data from the request
    data = request.get_json()

    if data is None:
        return jsonify({'error': 'No valid JSON data found in the request.'}), 400

    baseline = data.get("baseline", "")
    current = data.get("current", "")

    summary_accepted = data.get("summary_accepted", False)
    if baseline == "" or current == "":
        return jsonify({'error': 'Baseline or Current missing.'}), 400
    
    try:
        # Call the LLM endpoint and get the response
        results = get_response_from_llm(
            baseline=baseline,
            current=current,
            summary_accepted=summary_accepted
        )

        print("\nOutput: ", results)

        # Return the response in JSON format
        return {
            "response" : results,
            "message" : "Score"
        }
    except Exception as e:
        # Print the error for debugging purposes
        print("Error in /get-score route:", e)
        # Return the error in JSON format
        return jsonify({'error': str(e)}), 500




