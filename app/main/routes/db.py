from flask import request
from flask_restx import Namespace, Resource
  
from app.main.swagger_models.db import (
    error_response_model,
    input_create_key_token_model, output_create_key_token_model,
    input_add_qa_request_model, add_qna_output_model, 
    input_set_baseline_model, success_response_model,
    input_update_qa_model, success_qa_model,
    output_get_usage_model,
    output_get_set_ids_model,
    output_get_project_ids_model,
    output_get_specific_project_model,
    input_create_project_model, output_create_project_model,
    output_delete_project_model, 
    output_update_project_name_model,
    output_delete_qa_set_model,
    compare_qa_sets_model, response_compare_qa_sets_model,
    input_save_qa_scores_model, response_save_qa_scores_model
)
from app.main.db_utils import (
    add_qa, update_qa, delete_qa_set,
    update_key_token,
    update_baseline, 
    get_usage_details,
    get_set_ids, get_project_ids,
    get_specific_project_details,
    create_project, delete_project,
    update_project_name,
    compare_qa_sets,
    save_qa_scores
)

db_ns = Namespace(
    name="Db",
    description="Db NS",
    path='/'
)

@db_ns.route("/create-key-token")
class CreateKeyToken(Resource):
    @db_ns.expect(input_create_key_token_model)
    @db_ns.doc(
        description="Retrieve and create a unique key token for a given email.",
    )
    @db_ns.response(200, "Success", output_create_key_token_model)
    @db_ns.response(
        400, "Quota exceeded / Invalid input / Not found", error_response_model
    )
    @db_ns.response(500, "Internal Server Error", error_response_model)
    def post(self):
        """
        Retrieve and create a unique key token for a given email. It will create a new data document if the email is not found.
        - **email**: User's email address.
        """
        data = request.get_json()

        if not data or "email" not in data:
            return {"error": "Invalid input, 'email' key is required"}, 400

        email = data["email"]

        try:
            result, new_key_token = update_key_token(email)
        except Exception as e:
            return {"error": str(e)}, 500
        
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

@db_ns.route("/create-project")
class CreateProject(Resource):
    @db_ns.response(200, "Success", output_create_project_model)
    @db_ns.response(400, "Invalid input / Not found", error_response_model)
    @db_ns.response(500, "Internal Server Error", error_response_model)
    @db_ns.expect(input_create_project_model)
    @db_ns.doc(
        description="Create project for user.",
        params={
            "key-token": {
                "description": "User identification token",
                "in": "header",
                "type": "string",
                "required": True,
            }
        },
    )
    def post(self):
        """
        Create project for user.
        **project_name (str)**: Name of the project
        """
        key_token = request.headers.get("key-token")
        if not key_token:
            return {"error": "Missing key token."}, 400

        data = request.get_json()

        if data is None or "project_name" not in data:
            return {"error": "Invalid input, required parameter is missing"}, 400

        project_name = data["project_name"]

        try:
            # create project against the user.
            result = create_project(key_token=key_token, project_name=project_name)
        except Exception as e:
            print("Error in /create-project:", e)
            return {"error": f"{str(e)}"}, 400

        project_id = list(result.keys())[0]
        return {
            "response": {"project_id": project_id, "project_name": project_name}
        }, 200

@db_ns.route("/add-qna")
class AddQnA(Resource):
    @db_ns.expect(input_add_qa_request_model)
    @db_ns.doc(
        description="Add a new QA set for a given email.",
        params={
            "key-token": {
                "description": "User identification token",
                "in": "header",
                "type": "string",
                "required": True,
            }
        },
    )
    @db_ns.response(200, "Success", add_qna_output_model)
    @db_ns.response(400, "Invalid input / Not found", error_response_model)
    @db_ns.response(500, "Internal Server Error", error_response_model)
    def post(self):
        """
        Adds a new QA set for the given email.
        - **qa_data**: QA data object with set_id
        """
        key_token = request.headers.get("key-token")
        if not key_token:
            return {"error": "Missing key token."}, 400

        data = request.get_json()
        if not data or ("project_id" not in data and "qa_data" not in data):
            return {"error": "Invalid input, required parameter is missing"}, 400

        qa_data = data["qa_data"]
        project_id = data["project_id"]

        try:
            # adding QA to db
            add_qa(key_token=key_token, project_identifier=project_id, qa_data=qa_data)
            print(f"QA set added against: {key_token} successfully.")
            return {"response": f"QA set added successfully."}, 200
        except Exception as e:
            print(f"Error in /set-qa: {str(e)}")
            return {"error": str(e)}, 400

@db_ns.route("/set-baseline")
class SetBaseline(Resource):
    @db_ns.expect(input_set_baseline_model)
    @db_ns.doc(
        description="Set provided set as a baseline for a given email and project id.",
        params={
            "key-token": {
                "description": "User identification token",
                "in": "header",
                "type": "string",
                "required": True,
            }
        },
    )
    @db_ns.response(200, "Success", success_response_model)  # Success response
    @db_ns.response(
        400, "Invalid input / Not found", error_response_model
    )  # Invalid input or not found
    @db_ns.response(500, "Internal Server Error", error_response_model)  # Server error
    def put(self):
        """
        Update the baseline to the given set ID.
        - **set_id**: QA set ID
        """
        key_token = request.headers.get("key-token")
        if not key_token:
            return {"error": "Missing key token."}, 400

        data = request.get_json()
        if not data or ("set_id" not in data and "project_id" not in data):
            return {"error": "Invalid input, required parameter is missing"}, 400

        set_id = data["set_id"]
        project_id = data["project_id"]

        try:
            # setting baseline (replace this with your actual logic)
            update_baseline(
                key_token=key_token, project_identifier=project_id, set_id=set_id
            )
            return {"response": f"Baseline updated against: {key_token}"}, 200
        except ValueError as e:
            # Assuming a custom exception like ValueError for this case
            return {"error": f"Error: {str(e)}"}, 400
        except Exception as e:
            # Handling any general exceptions
            print("Error in /set-baseline:", str(e))
            return {"error": f"{str(e)}"}, 500

@db_ns.route("/update-qna")
class UpdateQnA(Resource):
    @db_ns.expect(input_update_qa_model)
    @db_ns.doc(
        description="Update an existing QA set for a given user.",
        params={
            "key-token": {
                "description": "User identification token",
                "in": "header",
                "type": "string",
                "required": True,
            }
        },
    )
    @db_ns.response(200, "Success", success_qa_model)
    @db_ns.response(400, "Invalid input / Not found", error_response_model)
    @db_ns.response(500, "Internal Server Error", error_response_model)
    def put(self):
        """
        Update an existing QA set for a given email.
        - **qa_data**: QA data object with set_id
        """
        key_token = request.headers.get("key-token")
        if not key_token:
            return {"error": "Missing key token."}, 400

        # Get JSON data from the request
        data = request.get_json()

        # Input parameter validation
        if not data or "qa_data" not in data or "project_id" not in data:
            return {"error": "Invalid input, required parameter is missing"}, 400

        qa = data["qa_data"]
        project_id = data["project_id"]

        try:
            # Attempt to update the QA set
            update_qa(key_token=key_token, project_identifier=project_id, qa_data=qa)
        except Exception as e:
            print("Error in /update-qa route:", e)
            return {"error": f"{str(e)}"}, 400

        return {"response": f"QA set updated against: {key_token} successfully."}, 200

@db_ns.route("/delete-qa-set")
class DeleteQaSet(Resource):
    @db_ns.response(200, "Success", output_delete_qa_set_model)
    @db_ns.response(400, "Invalid input / Not found", error_response_model)
    @db_ns.response(500, "Internal Server Error", error_response_model)
    @db_ns.doc(
        description="Delete QA set for user.",
        params={
            "key-token": {
                "description": "User identification token",
                "in": "header",
                "type": "string",
                "required": True,
            },
            "set_id": {
                "description": "QA set ID",
                "in": "query",
                "type": "integer",
                "required": True,
            },
            "project_id": {
                "description": "Project ID",
                "in": "query",
                "type": "integer",
                "required": True,
            },
        },
    )
    def delete(self):
        """
        Delete QA set for user.
        """
        key_token = request.headers.get("key-token")
        if not key_token:
            return {"error": "Missing key token."}, 400

        set_id = request.args.get("set_id")
        if not set_id:
            return {"error": "Missing set id."}, 400
        
        project_id = request.args.get("project_id")
        if not project_id:
            return {"error": "Missing project id."}, 400

        try:
            set_id = int(set_id)
        except ValueError:
            return {"error": "Invalid set id."}, 400

        try:
            delete_qa_set(key_token=key_token, set_id=set_id, project_identifier=project_id)
        except Exception as e:
            print("Error in /delete-qa-set:", e)
            return {"error": f"{str(e)}"}, 400

        return {"message": "QA set deleted"}, 200

@db_ns.route("/get-usage-details")
class GetUsageDetails(Resource):
    @db_ns.doc(
        description="Get usage details for a given email and project ID.",
        params={
            "key-token": {
                "description": "User identification token",
                "in": "header",
                "type": "string",
                "required": True,
            }
        },
    )
    @db_ns.response(200, "Success", output_get_usage_model)
    @db_ns.response(400, "Invalid input / Not found", error_response_model)
    @db_ns.response(500, "Internal Server Error", error_response_model)
    def get(self):
        """
        Get usage details for a given user.
        """
        key_token = request.headers.get("key-token")
        if not key_token:
            return {"error": "Missing key token."}, 400

        try:
            # Call your function to fetch usage details (the result would be dynamic based on the DB)
            result = get_usage_details(key_token=key_token)
        except Exception as e:
            print("Error in /get-usage-details:", e)
            return {"error": f"{str(e)}"}, 500

        return {
            "response": result,
            "message": "Usage details retrieved.",
        }, 200
    
@db_ns.route("/get-set-ids")
class GetSetIds(Resource):
    @db_ns.response(200, "Success", output_get_set_ids_model)
    @db_ns.response(400, "Invalid input / Not found", error_response_model)
    @db_ns.response(500, "Internal Server Error", error_response_model)
    @db_ns.doc(
        description="Get set ids for user.",
        params={
            "key-token": {
                "description": "User identification token",
                "in": "header",
                "type": "string",
                "required": True,
            },
            "project_id": {
                "description": "Project ID",
                "in": "query",
                "type": "integer",
                "required": True,
            },
        },
    )
    def get(self):
        """
        Get set ids for user.
        """
        key_token = request.headers.get("key-token")
        if not key_token:
            return {"error": "Missing key token."}, 400

        project_id = request.args.get("project_id")
        if not project_id:
            return {"error": "Missing project id."}, 400

        try:
            # Call your function to fetch usage details (the result would be dynamic based on the DB)
            result = get_set_ids(key_token=key_token, project_identifier=project_id)
        except Exception as e:
            print("Error in /get-set-ids:", e)
            return {"error": f"{str(e)}"}, 00

        return {
            "response": result,
            "message": "Set IDs retreived",
        }, 200
    
@db_ns.route("/get-project-ids")
class GetProjectIds(Resource):
    @db_ns.response(200, "Success", output_get_project_ids_model)
    @db_ns.response(400, "Invalid input / Not found", error_response_model)
    @db_ns.response(500, "Internal Server Error", error_response_model)
    @db_ns.doc(
        description="Get project ids and there respective data for the user.",
        params={
            "key-token": {
                "description": "User identification token",
                "in": "header",
                "type": "string",
                "required": True,
            }
        },
    )
    def get(self):
        """
        Get project ids and there respective data for the user.
        """
        key_token = request.headers.get("key-token")
        if not key_token:
            return {"error": "Missing key token."}, 400

        try:
            # function to fetch all the projects data
            result = get_project_ids(key_token=key_token)
        except Exception as e:
            print("Error in /get-set-ids:", e)
            return {"error": f"{str(e)}"}, 00

        return {
            "project_data": result,
            "message": "Projects data retreived",
        }, 200
    
@db_ns.route("/get-specific-project-details")
class GetSpecificProject(Resource):
    @db_ns.response(200, "Success", output_get_specific_project_model)
    @db_ns.response(400, "Invalid input / Not found", error_response_model)
    @db_ns.response(500, "Internal Server Error", error_response_model)
    @db_ns.doc(
        description="Get specific project and there respective data for the user.",
        params={
            "key-token": {
                "description": "User identification token",
                "in": "header",
                "type": "string",
                "required": True,
            },
            "project_id": {
                "description": "Project ID",
                "in": "query",
                "type": "integer",
                "required": True,
            },
        },
    )
    def get(self):
        """
        Get specific project and there respective data for the user.
        """
        key_token = request.headers.get("key-token")
        if not key_token:
            return {"error": "Missing key token."}, 400

        project_id = request.args.get("project_id")
        if not project_id:
            return {"error": "Missing project id."}, 400
        try:
            # function to fetch all the projects data
            result = get_specific_project_details(
                key_token=key_token, project_identifier=project_id
            )
        except Exception as e:
            print("Error in /get-set-ids:", e)
            return {"error": f"{str(e)}"}, 00

        return {
            "project_data": result,
            "message": "Projects data retreived",
        }, 200

@db_ns.route("/delete-project")
class DeleteProject(Resource):
    @db_ns.response(200, "Success", output_delete_project_model)
    @db_ns.response(400, "Invalid input / Not found", error_response_model)
    @db_ns.response(500, "Internal Server Error", error_response_model)
    @db_ns.doc(
        description="Delete project for user.",
        params={
            "key-token": {
                "description": "User identification token",
                "in": "header",
                "type": "string",
                "required": True,
            },
            "project_id": {
                "description": "Project ID",
                "in": "query",
                "type": "integer",
                "required": True,
            },
        },
    )
    def delete(self):
        """
        Delete project for user.
        """
        key_token = request.headers.get("key-token")
        if not key_token:
            return {"error": "Missing key token."}, 400

        project_id = request.args.get("project_id")
        if not project_id:
            return {"error": "Missing project id."}, 400

        try:
            # Call your function to fetch usage details (the result would be dynamic based on the DB)
            delete_project(key_token=key_token, project_id=project_id)
        except Exception as e:
            print("Error in /delete-project:", e)
            return {"error": f"{str(e)}"}, 500

        return {"message": "Project deleted"}, 200
    
@db_ns.route("/update-project-name")
class UpdateProjectName(Resource):
    @db_ns.response(200, "Success", output_update_project_name_model)
    @db_ns.response(400, "Invalid input / Not found", error_response_model)
    @db_ns.response(500, "Internal Server Error", error_response_model)
    @db_ns.doc(
        description="Update project name for user.",
        params={
            "key-token": {
                "description": "User identification token",
                "in": "header",
                "type": "string",
                "required": True,
            },
            "project_id": {
                "description": "Project ID",
                "in": "query",
                "type": "integer",
                "required": True,
            },
            "project_name": {
                "description": "Project name",
                "in": "query",
                "type": "string",
                "required": True,
            },
        },
    )
    def put(self):
        """
        Update project name for user.
        """
        key_token = request.headers.get("key-token")
        if not key_token:
            return {"error": "Missing key token."}, 400

        project_id = request.args.get("project_id")
        if not project_id:
            return {"error": "Missing project id."}, 400

        project_name = request.args.get("project_name")
        if not project_name:
            return {"error": "Missing project name."}, 400

        try:
            # Call your function to fetch usage details (the result would be dynamic based on the DB)
            update_project_name(
                key_token=key_token, project_id=project_id, project_name=project_name
            )
        except Exception as e:
            print("Error in /update-project-name:", e)
            return {"error": f"{str(e)}"}, 500

        return {"message": "Project name updated to " + project_name}
    
@db_ns.route("/compare-qna-sets")
class CompareQnASets(Resource):
    @db_ns.expect(compare_qa_sets_model)
    @db_ns.doc(
        description="Compare two QA sets for a user.",
        params={
            "key-token": {
                "description": "User identification token",
                "in": "header",
                "type": "string",
                "required": True,
            }
        },
    )
    @db_ns.response(200, "Success", response_compare_qa_sets_model)
    @db_ns.response(400, "Invalid input / Not found", error_response_model)
    @db_ns.response(500, "Internal Server Error", error_response_model)
    def post(self):
        """
        Compare two QA sets for a user.
        - **current_set_id**: ID of the current QA set
        - **baseline_set_id**: (optional) ID of the baseline QA set
        - **project_id**: ID of the project
        """
        key_token = request.headers.get("key-token")
        if not key_token:
            return {"error": "Missing key token."}, 400

        # Get JSON data from the request
        data = request.get_json()

        # Input parameter validation
        if not data or ("current_set_id" not in data and "project_id" not in data):
            return {"error": "Invalid input, required parameter is missing"}, 400

        project_id = data["project_id"]
        current_set_id = data["current_set_id"]
        baseline_set_id = data.get("baseline_set_id", None)

        try:
            result = compare_qa_sets(
                key_token=key_token,
                current_set_id=current_set_id,
                baseline_set_id=baseline_set_id,
                project_identifier=project_id,
            )
        except Exception as e:
            print("Error in /compare-qa-sets:", e)
            return {"error": f"{str(e)}"}, 400

        return {
            "response": result,
            "message": "Scores calculated for the current set.",
        }, 200  
    
@db_ns.route("/save-qna-scores")
class SaveQnAScores(Resource):
    @db_ns.expect(input_save_qa_scores_model)
    @db_ns.doc(
        description="Save QA scores for a user.",
        params={
            "key-token": {
                "description": "User identification token",
                "in": "header",
                "type": "string",
                "required": True,
            }
        },
    )
    @db_ns.response(200, "Success", response_save_qa_scores_model)
    @db_ns.response(400, "Invalid input / Not found", error_response_model)
    @db_ns.response(500, "Internal Server Error", error_response_model)
    def post(self):
        """
        Save QA scores for a user.
        - **set_id**: ID of the QA set
        - **project_id**: ID of the project
        - **qa_scores_data**: QnA scores
        """
        key_token = request.headers.get("key-token")
        if not key_token:
            return {"error": "Missing key token."}, 400

        # Get JSON data from the request
        data = request.get_json()

        # Input parameter validation
        if not data or ("set_id" not in data and "project_id" not in data or "qa_scores_data" not in data):
            return {"error": "Invalid input, required parameter is missing"}, 400

        project_id = data["project_id"]
        set_id = data["set_id"]
        qa_scores_data = data["qa_scores_data"]

        try:
            save_qa_scores(
                key_token=key_token,
                set_id=set_id,
                project_identifier=project_id,
                qa_scores=qa_scores_data
            )
        except Exception as e:
            print("Error in /save-qa-scores:", e)
            return {"error": f"{str(e)}"}, 400

        return {
            "message": "Scores saved sucessfully.", 
        }, 200