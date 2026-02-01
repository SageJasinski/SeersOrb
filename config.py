"""Application configuration settings."""
import os
from pathlib import Path


class Config:
    """Base configuration."""
    
    # Application
    APP_NAME = "Seer's Orb"
    VERSION = "0.1.0"
    DEBUG = False
    
    # Paths
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"
    DECKS_DIR = DATA_DIR / "decks"
    CACHE_DIR = DATA_DIR / "cache"
    
    # Scryfall API
    SCRYFALL_API_BASE = "https://api.scryfall.com"
    SCRYFALL_RATE_LIMIT_MS = 100  # milliseconds between requests
    CARD_CACHE_TTL_HOURS = 24
    
    # Monte Carlo
    DEFAULT_SIMULATION_ITERATIONS = 10000
    MAX_SIMULATION_ITERATIONS = 100000
    
    # Graph Analysis
    DEFAULT_DECK_SIZE = 99  # Commander format
    OPENING_HAND_SIZE = 7
    
    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-in-production")


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


# Configuration mapping
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}


def get_config(env: str = None) -> Config:
    """Get configuration based on environment."""
    if env is None:
        env = os.environ.get("FLASK_ENV", "default")
    return config.get(env, config["default"])
