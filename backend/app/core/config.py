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


@lru_cache
def get_settings() -> Settings:
    storage_dir = Path(os.getenv("STORAGE_DIR", BACKEND_DIR / "storage")).resolve()
    upload_dir = Path(os.getenv("UPLOAD_DIR", storage_dir / "uploads")).resolve()
    projects_dir = Path(os.getenv("PROJECTS_DIR", storage_dir / "projects")).resolve()

    # The MVP keeps state local and temporary, so these folders are created on boot.
    upload_dir.mkdir(parents=True, exist_ok=True)
    projects_dir.mkdir(parents=True, exist_ok=True)

    return Settings(
        project_name=os.getenv("PROJECT_NAME", "Project Study IA"),
        api_prefix=os.getenv("API_PREFIX", "/api"),
        cors_origins=_split_csv(
            os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
        ),
        storage_dir=storage_dir,
        upload_dir=upload_dir,
        projects_dir=projects_dir,
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_chat_model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
    )
