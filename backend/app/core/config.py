from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import os

BACKEND_DIR = Path(__file__).resolve().parents[2]

try:
    from dotenv import load_dotenv

    load_dotenv(BACKEND_DIR / ".env")
except ImportError:
    pass


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _resolve_env_path(value: str | None, default: Path) -> Path:
    """Resolve paths relative to the backend directory, not the process CWD."""
    if not value:
        return default.resolve()
    path = Path(value)
    if not path.is_absolute():
        path = BACKEND_DIR / path
    return path.resolve()


@dataclass(frozen=True)
class Settings:
    project_name: str
    api_prefix: str
    cors_origins: list[str]
    storage_dir: Path
    upload_dir: Path
    projects_dir: Path
    openai_api_key: str
    openai_chat_model: str
    openai_embed_model: str
    openai_base_url: str
    ollama_base_url: str
    ollama_model: str
    ollama_embed_model: str
    nim_api_key: str
    nim_base_url: str
    nim_model: str
    nim_fallback_model: str
    nim_embed_model: str
    ai_provider: str
    ai_timeout_seconds: float


@lru_cache
def get_settings() -> Settings:
    storage_dir = _resolve_env_path(os.getenv("STORAGE_DIR"), BACKEND_DIR / "storage")
    upload_dir = _resolve_env_path(os.getenv("UPLOAD_DIR"), storage_dir / "uploads")
    projects_dir = _resolve_env_path(os.getenv("PROJECTS_DIR"), storage_dir / "projects")

    # The MVP keeps state local and temporary, so these folders are created on boot.
    upload_dir.mkdir(parents=True, exist_ok=True)
    projects_dir.mkdir(parents=True, exist_ok=True)

    return Settings(
        project_name=os.getenv("PROJECT_NAME", "Project Study IA"),
        api_prefix=os.getenv("API_PREFIX", "/api"),
        cors_origins=_split_csv(
            os.getenv("CORS_ORIGINS", "*")
        ),
        storage_dir=storage_dir,
        upload_dir=upload_dir,
        projects_dir=projects_dir,
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_chat_model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        openai_embed_model=os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small"),
        openai_base_url=os.getenv("OPENAI_BASE_URL", ""),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.2"),
        ollama_embed_model=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
        nim_api_key=os.getenv("NVIDIA_API_KEY", os.getenv("NIM_API_KEY", "")),
        nim_base_url=os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1"),
        nim_model=os.getenv("NIM_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b"),
        nim_fallback_model=os.getenv("NIM_FALLBACK_MODEL", "nvidia/nemotron-3-ultra-550b-a55b"),
        nim_embed_model=os.getenv("NIM_EMBED_MODEL", "nvidia/nv-embedqa-e5-v5"),
        ai_provider=os.getenv("AI_PROVIDER", "").lower(),
        ai_timeout_seconds=float(os.getenv("AI_TIMEOUT_SECONDS", "300") or 300),
    )
