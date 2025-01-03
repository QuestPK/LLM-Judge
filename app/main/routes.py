from flask import Blueprint, render_template, jsonify, request
from flasgger import Swagger
from .utils import get_response_from_llm

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return "Hi, home page!"

@main_bp.route('/chat', methods=['POST'])
def chat():
    # Get the data from the request
    data = request.get_json()

    if data is None:
        return jsonify({'error': 'No valid JSON data found in the request.'}), 400

    messages = data.get("messages", [])
    if not isinstance(messages, list) or len(messages) == 0:
        return jsonify({'error': 'No messages found in the request or invalid format.'}), 400
    
    try:
        # Call the LLM endpoint and get the response
        results = get_response_from_llm(messages)

        print("\nOutput: ", results)

        # Return the response in JSON format
        return {
            "response" : results,
            "message" : "Score"
        }
    except Exception as e:
        # Print the error for debugging purposes
        print("Error in /chat route:", e)
        # Return the error in JSON format
        return jsonify({'error': str(e)}), 500


# {
#     "messages": [
#         {
#             "role": "user",
#             "content": user_message
#         },
# }

# succuss = {
#     "response" :str
# }
# error = {
#     "error": str
# }
