from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    with app.app_context():
        # Import and register blueprints
        from app.main import routes
        app.register_blueprint(routes.main_bp)

        return app
