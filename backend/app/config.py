from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"

    app_api_key: str = "dev-local-key"
    cors_origins: str = "http://localhost:3000"

    data_dir: str = "data"
    vector_index_path: str = "data/faiss_index"
    db_path: str = "data/medisense.db"
    medlineplus_cache_path: str = "data/medlineplus_topics.json"

    embedding_model: str = "BAAI/bge-small-en-v1.5"
    chunk_size: int = 800
    chunk_overlap: int = 120
    retrieval_top_k: int = 4

    triage_adapter_path: str = "finetuning/artifacts/triage-lora"
    triage_base_model: str = "distilbert-base-uncased"

    rate_limit_per_minute: int = 20

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
