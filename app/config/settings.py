from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "水质三维智能监测与分析系统"
    DEBUG: bool = True

    # MySQL
    DATABASE_URL: str = "mysql+aiomysql://root:123456@localhost:3306/water_quality"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Milvus
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "water-analysis"
    MINIO_SECURE: bool = False

    # LLM
    LLM_PROVIDER: str = "deepseek"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-v4-flash"

    # JWT
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 2
    USER_AUTHORIZATION: str = "False"

    # Storage
    UPLOAD_DIR: str = "./app/data/uploads"
    REPORT_DIR: str = "./app/data/reports"
    STATIC_DIR: str = "./app/static"
    THREED_DIR: str = "./app/data/3d"

    # Spatial
    GRID_RESOLUTION: int = 50
    INTERPOLATION_METHOD: str = "idw"
    LON_MIN: float = 73
    LON_MAX: float = 135
    LAT_MIN: float = 3
    LAT_MAX: float = 54
    DEPTH_MIN: float = 0
    DEPTH_MAX: float = 50

    # Anomaly
    CONTAMINATION: float = 0.05
    CHL_MIN: float = 0.0
    CHL_MAX: float = 20.0
    ODO_MIN: float = 4.0
    ODO_MAX: float = 12.0
    PH_MIN: float = 6.5
    PH_MAX: float = 8.5
    TURB_MIN: float = 0.0
    TURB_MAX: float = 10.0
    TEMP_MIN: float = 0.0
    TEMP_MAX: float = 35.0

    # Log
    LOG_LEVEL: str = "INFO"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
