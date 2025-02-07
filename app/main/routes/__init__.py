from app.main.routes.judge import judge_ns
from app.main.routes.db import db_ns

def register_namespaces(api):
    api.add_namespace(judge_ns)
    api.add_namespace(db_ns)
