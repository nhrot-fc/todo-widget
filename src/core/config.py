from pydantic_settings import BaseSettings


class Config(BaseSettings):
    # Application
    app_name: str = "Todo Widget"
    storage_path: str = "tasks.json"

    # Logging
    log_level: str = "DEBUG"
    log_file: str | None = None



settings = Config()
