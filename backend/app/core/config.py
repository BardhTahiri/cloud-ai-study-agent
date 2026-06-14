import os

from dotenv import find_dotenv, load_dotenv


load_dotenv(find_dotenv())


class Settings:
    app_name: str = os.getenv("APP_NAME", "Cloud AI Study Agent")
    app_env: str = os.getenv("APP_ENV", "development")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./storage/cloud_ai_study_agent.db")
    storage_provider: str = os.getenv("STORAGE_PROVIDER", "local")
    local_storage_path: str = os.getenv("LOCAL_STORAGE_PATH", "./storage/uploads")


settings = Settings()
