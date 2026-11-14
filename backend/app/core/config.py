from pydantic_settings import BaseSettings
from pathlib import Path

# 读取 backend/ 同级的根目录 .env（D:\Python全栈AI答题小程序\.env）
_ROOT_ENV = Path(__file__).resolve().parent.parent.parent.parent / ".env"


class Settings(BaseSettings):
    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    deepseek_base_url: str = "https://api.deepseek.com"

    # Database
    database_url: str = "mysql+pymysql://root:password@127.0.0.1:3306/ai_quiz"

    # App
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    model_config = {
        "env_file": str(_ROOT_ENV),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


settings = Settings()
