import os

from dotenv import find_dotenv, load_dotenv


load_dotenv(find_dotenv())


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    app_name: str = os.getenv("APP_NAME", "Cloud AI Study Agent")
    app_env: str = os.getenv("APP_ENV", "development")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./storage/cloud_ai_study_agent.db")
    storage_provider: str = os.getenv("STORAGE_PROVIDER", "local")
    local_storage_path: str = os.getenv("LOCAL_STORAGE_PATH", "./storage/uploads")
    task_queue_mode: str = os.getenv("TASK_QUEUE_MODE", "local").strip().lower()
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    task_queue_fallback_local: bool = _env_bool("TASK_QUEUE_FALLBACK_LOCAL", True)
    agent_base_url: str = os.getenv("AGENT_BASE_URL", "http://localhost:8010").strip().rstrip("/")
    agent_api_key: str = os.getenv("AGENT_API_KEY", "")
    agent_http_timeout_seconds: float = float(os.getenv("AGENT_HTTP_TIMEOUT_SECONDS", "15"))


settings = Settings()
