from pydantic_settings import BaseSettings


class Config(BaseSettings):
    # Application
    app_name: str = "Todo Widget"
    storage_path: str = "tasks.json"

    # Logging
    log_level: str = "INFO"
    log_file: str | None = None

    # UI / Styling
    opacity: float = 1.0
    transparent_background: bool = True
    decorated: bool = True


settings = Config()
