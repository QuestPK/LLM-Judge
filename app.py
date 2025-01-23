from flask import Flask, request, jsonify
from flasgger import Swagger

app = Flask(__name__)
swagger = Swagger(app)

@app.route('/user', methods=['GET'])
def get_user():
    """
    Get user details
    ---
    responses:
      200:
        description: A successful response
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "This is a GET request for fetching user details"
    """
    return jsonify({"message": "This is a GET request for fetching user details"})

@app.route('/user', methods=['POST'])
def create_user():
    """
    Create a new user
    ---
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              name:
                type: string
                example: Alice
              age:
                type: integer
                example: 25
    responses:
      201:
        description: User created successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "User Alice of age 25 created successfully!"
    """
    data = request.json
    return jsonify({"message": f"User {data['name']} of age {data['age']} created successfully!"}), 201

if __name__ == '__main__':
    app.run(debug=True)
