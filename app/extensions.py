from flask_pymongo import PyMongo
from flask_restx import Api

mongo = PyMongo()
api = Api(
    version="1.2",
    title="API Documentation",
    description="",
    doc="/api-docs",
    default="Judge",
    default_label="Judge Namespace"
)