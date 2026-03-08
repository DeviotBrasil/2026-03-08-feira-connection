from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    ZMQ_ENDPOINT: str = Field(default="tcp://127.0.0.1:5555")
    HTTP_PORT: int = Field(default=8080)
    HTTP_HOST: str = Field(default="0.0.0.0")
    ICE_TIMEOUT: float = Field(default=3.0)
    ZMQ_CONNECTED_THRESHOLD_S: float = Field(default=2.0)
    LOG_LEVEL: str = Field(default="INFO")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
