from flask import Flask
from app.config import load_configurations, configure_logging
from .views import webhook_blueprint
from .whatsapp import whatsapp_blueprint


def create_app():
    app = Flask(__name__)

    # Load configurations and logging settings
    load_configurations(app)
    configure_logging()

    # Import and register blueprints
    app.register_blueprint(webhook_blueprint)
    app.register_blueprint(whatsapp_blueprint)  # Register the new whatsapp blueprint

    return app
