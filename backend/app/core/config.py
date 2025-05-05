# backend/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import ClassVar

class Settings(BaseSettings):
    """Loads and validates application settings."""

    # --- Database ---
    MONGODB_URI: str
    DB_NAME: str = "future_self_db" # Default database name

    # --- JWT ---
    SECRET_KEY: str # No default - MUST be provided in .env
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 # Default expiry: 30 minutes

    # --- Server (Optional) ---
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # --- Model Configuration ---
    # Tells Pydantic-Settings where to find the .env file
    # It looks for .env starting from the location of this config.py file
    # and going up the directory tree.
    # Assumes .env is in project_root/config/
    env_file_path: ClassVar[Path] = Path(__file__).parent.parent.parent.parent / "config" / ".env"

    model_config = SettingsConfigDict(
        env_file=str(env_file_path), # Convert Path to string for Pydantic
        env_file_encoding='utf-8',
        case_sensitive=True, # Match environment variable names exactly
        extra='ignore' # Ignore extra fields in the environment
    )

# Create a single instance of the settings to be imported by other modules
settings = Settings()

# Optional: Print loaded settings during startup (for debugging)
print(f"DEBUG: Loaded settings - MONGODB_URI set: {'*' * 5 if settings.MONGODB_URI else 'No'}")
print(f"DEBUG: Loaded settings - DB_NAME: {settings.DB_NAME}")
print(f"DEBUG: Loaded settings - SECRET_KEY set: {'*' * 5 if settings.SECRET_KEY else 'No'}")
print(f"DEBUG: Loaded settings - ALGORITHM: {settings.ALGORITHM}")
print(f"DEBUG: Loaded settings - ACCESS_TOKEN_EXPIRE_MINUTES: {settings.ACCESS_TOKEN_EXPIRE_MINUTES}")