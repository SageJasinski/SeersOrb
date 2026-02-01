"""Flask application factory."""
from flask import Flask
from flask_cors import CORS


def create_app(config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    if config:
        app.config.from_object(config)
    
    # Enable CORS for API calls
    CORS(app)
    
    # Ensure data directories exist
    _ensure_directories(app)
    
    # Register blueprints
    _register_blueprints(app)
    
    return app


def _ensure_directories(app):
    """Create required data directories if they don't exist."""
    from pathlib import Path
    
    config = app.config
    dirs = [
        config.get("DATA_DIR"),
        config.get("DECKS_DIR"),
        config.get("CACHE_DIR"),
    ]
    
    for dir_path in dirs:
        if dir_path:
            Path(dir_path).mkdir(parents=True, exist_ok=True)


def _register_blueprints(app):
    """Register application blueprints."""
    from app.routes import main, deck, analysis, simulation, api
    
    app.register_blueprint(main.bp)
    app.register_blueprint(deck.bp, url_prefix="/deck")
    app.register_blueprint(analysis.bp, url_prefix="/analysis")
    app.register_blueprint(simulation.bp, url_prefix="/simulation")
    app.register_blueprint(api.bp, url_prefix="/api")
