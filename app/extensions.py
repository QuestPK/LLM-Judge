from flask_pymongo import PyMongo
from flask_restx import Api

mongo = PyMongo()
api = Api(
    version="1.3",
    title="LLM Judge Api's",
    description="API's and there usage.",
    # doc="/api-docs",
)