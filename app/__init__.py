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

    # Test MongoDB Connection
    try:
        with app.app_context():  # Ensure we are within the application context
            mongo.db.command("ping")  # Perform a simple ping test
            print("✅ Successfully connected to MongoDB.")
    except Exception as e:
        print("❌ Error connecting to MongoDB:", e)
        raise  # Stop the application if MongoDB is not reachable

    # Register the main blueprint under the /register-doc prefix
    app.register_blueprint(main_bp)

    # Initialize the Flask-RESTx API
    api.init_app(app)

    return app
