
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    database_url: str
    rabbitmq_url: str

    # S3-compatible object storage
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = Field(validation_alias="MINIO_ROOT_USER")
    s3_secret_key: str = Field(validation_alias="MINIO_ROOT_PASSWORD")
    s3_bucket: str = Field(validation_alias="MINIO_BUCKET")
    s3_region: str = "us-east-1"

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
