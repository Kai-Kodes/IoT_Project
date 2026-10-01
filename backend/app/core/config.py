"""
P_311 Configuration Module
Centralized settings management using pydantic-settings.
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Base Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    KNOWLEDGE_BASE_DIR: Path = BASE_DIR / "knowledge_base"
    VECTOR_STORE_PATH: Path = BASE_DIR / "data" / "vector_store"
    DATABASE_PATH: str = str(BASE_DIR / "data" / "p311.db")

    # MQTT Settings
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_KEEPALIVE: int = 60
    MQTT_TELEMETRY_TOPIC_SUB: str = "p311/machine/+/telemetry"
    MQTT_COMMAND_TOPIC_PREFIX: str = "p311/machine"
    MQTT_STATUS_TOPIC_PREFIX: str = "p311/machine"
    MQTT_FAULT_TOPIC_PREFIX: str = "p311/machine"

    # Database Settings
    USE_POSTGRES: bool = True
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5433
    POSTGRES_DB: str = "p311_iot"
    POSTGRES_USER: str = "p311_admin"
    POSTGRES_PASSWORD: str = "p311_industrial_secret"
    POSTGRES_POOL_MIN: int = 2
    POSTGRES_POOL_MAX: int = 10
    DATABASE_PATH: str = str(BASE_DIR / "data" / "p311.db")
    TELEMETRY_RETENTION_LIMIT: int = 10000

    # Grafana Settings
    GRAFANA_PORT: int = 3000
    GRAFANA_URL: str = "http://localhost:3000"

    # Local LLM (Ollama) Settings
    LLM_MODEL: str = "qwen2.5:1.5b"
    LLM_BASE_URL: str = "http://localhost:11434"
    LLM_NUM_CTX: int = 2048
    LLM_TEMPERATURE: float = 0.1
    LLM_TIMEOUT_SECONDS: float = 45.0

    # Local RAG & Embedding Settings
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    RAG_TOP_K: int = 3
    RAG_MIN_SIMILARITY: float = 0.30

    # Machine Simulation
    DEFAULT_MACHINE_ID: str = "MOTOR-001"
    SIMULATOR_PUBLISH_INTERVAL: float = 1.0


settings = Settings()
