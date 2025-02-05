from flask import Flask

from app.config import Config
from app.extensions import mongo, api
from app.main.routes import main_bp  

def create_app():
    app = Flask(__name__)

    @app.route('/')
    def home():
        return """
        <h2>Hi, home page! Version: v1.1.0</h2>
        <br>
        <a href="/api-docs" target="_blank">View API Documentation</a>
        """
    
    app.config.from_object(Config)

    # Initialize MongoDB
    mongo.init_app(app)

    # Register the main blueprint under the /register-doc prefix
    app.register_blueprint(main_bp)
    
    # Initialize the Flask-RESTx API
    api.init_app(app)
    
    return app


