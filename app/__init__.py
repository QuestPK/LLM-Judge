from flask import Flask
from flask_pymongo import PyMongo
from app.config import Config

mongo = PyMongo()

def create_app():
    app = Flask(__name__)

    # Load config
    app.config.from_object(Config)

    mongo.init_app(app)

    @app.route('/')
    def home():
        return """
        <h2>Hi, home page! Version: v1.1.0</h2>
        <br>
        <a href="/api-docs" target="_blank">View API Documentation</a>
        """
    
    with app.app_context():
        # Import and register blueprints
        from app.main import routes
        app.register_blueprint(routes.main_bp)

        return app