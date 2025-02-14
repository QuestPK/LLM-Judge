from flask_restx import fields
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