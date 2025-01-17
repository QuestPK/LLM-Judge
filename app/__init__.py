from flask import Flask
from flask_pymongo import PyMongo
from app.config import Config

mongo = PyMongo()

def create_app():
    app = Flask(__name__)

    # Load config
    app.config.from_object(Config)

    mongo.init_app(app)

    with app.app_context():
        # Import and register blueprints
        from app.main import routes
        app.register_blueprint(routes.main_bp)

        return app
