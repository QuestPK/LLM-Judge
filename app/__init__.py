from flask import Flask
from flask import Blueprint

from app.config import Config
from app.extensions import mongo, api
from app.main.routes import register_namespaces

def create_app() -> Flask:
    """Create the Flask application and initialize the configuration."""
    app = Flask(__name__)

    app.config.from_object(Config)

    # Initialize MongoDB
    mongo.init_app(app)

    # Test MongoDB Connection
    try:
        with app.app_context():  # Ensure we are within the application context
            mongo.db.command("ping")  # Perform a simple ping test
            print("✅ Successfully connected to MongoDB.")
    except Exception as e:
        print("❌ Error connecting to MongoDB:", e)
        raise  # Stop the application if MongoDB is not reachable

    # Create the Blueprint for the main API
    main_bp = Blueprint("api", __name__)
    
    # Initialize the Flask-RESTx API
    api.init_app(main_bp)
    register_namespaces(api)

    # Register the Blueprint with the application
    app.register_blueprint(main_bp)
    return app