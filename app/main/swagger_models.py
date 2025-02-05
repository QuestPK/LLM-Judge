from flask_restx import Resource, fields, Namespace
from app.extensions import api

# model for error responses
error_response_model = api.model(
    "ErrorResponse",
    {
        "error": fields.String(description="Error message", example="Error details."),
    },
)

# /calculate-score
calculate_score_model = api.model(
    "CalculateScore",
    {
        "query_data": fields.Nested(
            api.model(
                "CalculateScoreQueryData",
                {
                    "question": fields.String(
                        required=True,
                        description="The question string",
                        example="What is capital of france?",
                    ),
                    "baseline": fields.String(
                        required=True,
                        description="The baseline string",
                        example="Paris",
                    ),
                    "current": fields.String(
                        required=True,
                        description="The current string",
                        example="I don't know",
                    ),
                },
            )
        ),
        "summary_accepted": fields.Boolean(
            required=False, description="Whether the summary is accepted", example=True
        ),
    },
)

output_score_model = api.model(
    "OutputCalculateScore",
    {
        "score": fields.Raw(
            description="Output get score data.",
            example={
                "score": "Integer Score",
                "reason": "Reason of score",
                "message": "API message",
            },
        ),
    },
)

# /calculate-score-for-queries
# input
cal_score_for_queries_model = api.model(
    "CalculateScoreForQueries",
    {
        "queries_data": fields.Nested(
            api.model(
                "CSForQueriesQueryItem",
                {
                    "123": fields.Nested(
                        api.model(
                            "CSFQIQueryDetails",
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
                        ),
                        example={
                            "question": "What is capital of france?",
                            "baseline": "Paris",
                            "current": "I don't know",
                        },
                    ),
                    "456": fields.Nested(
                        api.model(
                            "CSFQIQueryDetails",
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
                        ),
                        example={
                            "question": "What is capital of Pakistan?",
                            "baseline": "Islamabad",
                            "current": "Islamabad",
                        },
                    ),
                },
            )
        ),
    },
)
# output
response_cal_scores_for_queries = api.model(
    "OutputCalculateScoreForQueries",
    {
        "scores": fields.Raw(
            required=True,
            description="A dictionary containing score objects indexed by IDs",
            example={
                "123": {
                    "score": 1,
                    "reason": "The response is completely not relevant and does not provide the correct information.",
                },
                "456": {
                    "score": 1,
                    "reason": "The response is completely irrelevant and does not provide any correct information.",
                },
            },
        )
    },
)

# /create-key-token
# Input
input_create_key_token_model = api.model(
    "CreateKeyToken",
    {
        "email": fields.String(
            required=True, description="User email", example="test123@gmail.com"
        )
    },
)
# response
output_create_key_token_model = api.model(
    "OutputCreateKeyToken",
    {
        "message": fields.String(
            description="Success message", example="Email found. key_token updated."
        ),
        "key_token": fields.String(
            description="Generated key token", example="12345-abcdef-67890"
        ),
    },
)

# /add-qna
input_add_qa_request_model = api.model(
    "AddQnA",
    {
        "project_id": fields.String(
            required=True, description="The ID of the project", example=786
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
                    },
                    {
                        "id": 2,
                        "question": "What is the capital of Pakistan?",
                        "answer": "Pakistan",
                    },
                ],
                "set_id": 78,
            },
        ),
    },
)

add_qna_output_model = api.model(
    "AddQnAOutput",
    {
        "response": fields.String(
            description="Success message", example="QA set added successfully."
        ),
    },
)

# /set-baseline
# input data
input_set_baseline_model = api.model(
    "SetBaseline",
    {
        "set_id": fields.Integer(required=True, description="QA set ID", example=786),
        "project_id": fields.String(
            required=True, description="The ID of the project", example=786
        ),
    },
)
# responses
success_response_model = api.model(
    "OutputSetBaseline",
    {
        "response": fields.String(
            description="Success message", example="Baseline updated successfully"
        ),
    },
)

# /update-qna
# input
input_update_qa_model = api.model(
    "UpdateQnA",
    {
        "project_id": fields.String(
            required=True, description="The ID of the project", example=786
        ),
        "qa_data": fields.Raw(
            required=True,
            description="QA data to be updated (generic structure)",
            example={
                "qa_set": [
                    {
                        "id": 1,
                        "question": "what is the capital of Afghanistan?",
                        "answer": "kabul",
                    },
                    {
                        "id": 2,
                        "question": "what is the capital of India?",
                        "answer": "Delhi",
                    },
                ],
                "set_id": 78,
            },
        ),
    },
)
success_qa_model = api.model(
    "OutputUpdateQnA",
    {
        "response": fields.String(
            description="Success message", example="QA set updated successfully"
        ),
    },
)

# /compare-qna-sets
# Input
compare_qa_sets_model = api.model(
    "CompareQnASets",
    {
        "project_id": fields.String(
            required=True, description="The ID of the project", example=786
        ),
        "current_set_id": fields.Integer(
            required=True, description="The ID of the current QA set", example=786
        ),
        "baseline_set_id": fields.Integer(
            description="The ID of the baseline QA set (optional)",
            example=786,
            required=False,
        ),
    },
)

# Output
response_compare_qa_sets_model = api.model(
    "OutputCompareQnASets",
    {
        "response": fields.Raw(
            required=True,
            description="Response containing dynamic IDs with their details",
            example={
                12: {
                    "reason": "No reason",
                    "score": 0,
                    "question": "",
                    "baseline": "",
                    "current": "",
                },
                34: {
                    "reason": "No reason",
                    "score": 0,
                    "question": "",
                    "baseline": "",
                    "current": "",
                },
            },
        ),
        "message": fields.String(
            required=True, description="Response message", example="Update successful"
        ),
    },
)

# /get-usage-details
# output
output_get_usage_model = api.model(
    "OutputGetUsageDetails",
    {
        "response": fields.Raw(
            required=True,
            description="Usage details containing token, processing, and request data",
            example={
                "token_used": 710,
                "avg_input_token": 95,
                "avg_output_token": 141.67,
                "avg_processing_time": 25.39,
                "avg_queue_time": 25.39,
                "number_of_requests": 3,
                "last_request_processing_time": 25.82,
                "total_input_token": 285,
                "total_output_token": 425,
                "total_processing_time": 76.18,
                "total_queue_time": 76.16,
            },
        ),
        "message": fields.String(
            required=True,
            description="Response message",
            example="Usage details retrieved.",
        ),
    },
)

# /retrieve-answer-from-rag
# questions format
input_get_answer_from_rag_question_format = api.model(
    "QuestionGetAnswerFromRag",
    {
        "1": fields.String(description="Question 1", example="What is photosynthesis"),
        "2": fields.String(
            description="Question 2", example="What is the capital of France?"
        ),
    },
)

# input payload mdoel
input_get_answer_from_rag = api.model(
    "RetrieveAnswerFromRag",
    {
        "base_url": fields.String(
            required=True,
            description="Base URL of the (your)API",
            example="http://127.0.0.1:5000/",
        ),
        "questions": fields.Nested(
            input_get_answer_from_rag_question_format,
            required=True,
            description="A dictionary of questions with IDs as keys",
        ),
    },
)
# response model
response_get_answer_from_rag_model = api.model(
    "OutputRetrieveAnswerFromRag",
    {
        "answer": fields.Raw(
            description="Answers from rag",
            example={"1": "It's answer", "2": "It's answer"},
        )
    },
)

# /get-set-ids
output_get_set_ids_model = api.model(
    "OutputGetSetIds",
    {
        "response": fields.Raw(
            [
                {
                    "set_id": 23,
                    "qa_set": [
                        {
                            "id": 1,
                            "question": "question",
                            "answer": "answer",
                        },
                        {
                            "id": 2,
                            "question": "question",
                            "answer": "answer",
                        },
                    ],
                }
            ]
        )
    },
)

# /get-project-ids
output_get_project_ids_model = api.model(
    "OutputGetProjectIds",
    {
        "project_data": fields.Raw(
            {
                "project_id": 1,
                "project_name": "Project 1",
                "qa_sets": [
                    {
                        "set_id": 23,
                        "qa_set": [
                            {
                                "id": 1,
                                "question": "question",
                                "answer": "answer",
                            },
                            {
                                "id": 2,
                                "question": "question",
                                "answer": "answer",
                            },
                        ],
                    }
                ],
            }
        )
    },
)

# /get-specific-project-details
output_get_specific_project_model = api.model(
    "OutputGetSpecificProject",
    {
        "project_data": fields.Raw(
            [
                {
                    "project_id": 1,
                    "project_name": "Project 1",
                    "qa_sets": [
                        {
                            "set_id": 23,
                            "qa_set": [
                                {
                                    "id": 1,
                                    "question": "question",
                                    "answer": "answer",
                                },
                                {
                                    "id": 2,
                                    "question": "question",
                                    "answer": "answer",
                                },
                            ],
                        }
                    ],
                }
            ]
        )
    },
)

# /create-project
input_create_project_model = api.model(
    "CreateProject",
    {
        "project_name": fields.String(
            required=True, description="Project name", example="Project 1"
        )
    },
)
output_create_project_model = api.model(
    "OutputCreateProject",
    {
        "message": fields.Raw(example="Created Project.",description="Project created successfully")
    }
)

# /delete-project
output_delete_project_model = api.model(
    "OutputDeleteProject",
    {
        "message": fields.Raw(example="Deleted Project.",description="Project deleted successfully")
    }
)

# /update-project-name
output_update_project_name_model = api.model(
    "OutputUpdateProjectName",
    {
        "message": fields.Raw(example="Updated Project Name to this.",description="Project name updated successfully")
    }
)

# /delete-qa-set
output_delete_qa_set_model = api.model(
    "output_delete_qa_set_model",
    {
        "message": fields.Raw(example="Deleted QA set.")
    }
)