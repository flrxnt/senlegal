from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Service
    host: str = "0.0.0.0"
    port: int = 8001
    cors_origins: str = "http://localhost:3000,http://localhost:8000"

    # Modèles
    model_name: str = "gemma4:31b-cloud"
    embed_model: str = "intfloat/multilingual-e5-small"
    ollama_host: str = "https://ollama.com"
    ollama_api_key: str | None = None
    # Durée pendant laquelle Ollama garde le modèle chargé en mémoire après
    # une requête. Format accepté par Ollama : "30m", "2h", "-1" (toujours
    # chargé), "0" (déchargé immédiatement). Accélère considérablement les
    # requêtes suivantes en évitant le cold start.
    ollama_keep_alive: str = "30m"

    # Données
    assets_dir: str = "./assets"
    chroma_dir: str = "./data/chroma"
    processed_dir: str = "./data/processed"
    collection_name: str = "senlegal_v1"

    # Retrieval
    top_k: int = 5
    min_score: float = 0.35
    max_chunk_chars: int = 1500
    query_rewrite_enabled: bool = True
    keyword_extraction_enabled: bool = True

    # Génération
    max_new_tokens: int = 512
    temperature: float = 0.1
    repetition_penalty: float = 1.1

    # Sécurité
    admin_token: str = "change-me"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def assets_path(self) -> Path:
        return Path(self.assets_dir).resolve()

    @property
    def chroma_path(self) -> Path:
        p = Path(self.chroma_dir).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def processed_path(self) -> Path:
        p = Path(self.processed_dir).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p


@lru_cache
def get_settings() -> Settings:
    return Settings()
