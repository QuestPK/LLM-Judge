from app import create_app

app = create_app()

# from judge_qna_handler.handler import JudgeQnaHandler
# handler = JudgeQnaHandler()

# import random
# # Function to generate a random number between min and max
# def generate_random_number(min, max):
#     return f"{random.randint(min, max)}"

# # Define your query response function
# def get_query_response(query: str) -> str:
#     # Add your query processing logic here
#     # This function should return the answer as a string
#     return "Answer: " + generate_random_number(1, 100) 

# # Create the endpoint
# handler.create_rag_response_endpoint(
#     app=app,
#     get_query_response=get_query_response
# )

if __name__ == '__main__':
    # app.run(debug=True, host='127.0.0.1', port=5000)
    app.run()
