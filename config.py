from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    The global settings for the messaging app.

    Attributes:
        DEBUG: If the messaging app is operating in debug mode or not.
        HOST: The host of the messaging app.
        PORT: The port of the messaging app.
    """

    TITLE: str = "Messaging App"
    DESCRIPTION: str = "A messaging app for secure communication."
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    KEY_LENGTH: int = 2048
    MAX_MESSAGE_SIZE: int = 1024

    model_config = SettingsConfigDict(env_file=".env", cli_parse_args=True)


@lru_cache
def get_settings():
    """Get the global app settings.

    Returns:
        The global app settings.
    """
    return Settings()