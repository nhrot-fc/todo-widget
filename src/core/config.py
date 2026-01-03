from pydantic_settings import BaseSettings


class Config(BaseSettings):
    # Application
    app_name: str = "todowidget"
    storage_path: str = "tasks.json"

    # Logging
    log_level: str = "INFO"
    log_file: str | None = None


settings = Config()
