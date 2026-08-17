import os

from dotenv import find_dotenv, load_dotenv


load_dotenv(find_dotenv())


class WorkerSettings:
    app_name: str = os.getenv("AGENT_APP_NAME", "Cloud AI Study Agent Worker")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    api_key: str = os.getenv("AGENT_API_KEY", "")
    result_expires_seconds: int = int(os.getenv("AGENT_RESULT_EXPIRES_SECONDS", "604800"))


settings = WorkerSettings()
