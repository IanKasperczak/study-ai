import json
from pathlib import Path
from threading import Lock

from app.core.config import get_settings
from app.models.schemas import FileSummary, Topic

settings = get_settings()


class StudyStore:
    def __init__(self, projects_dir: Path) -> None:
        self.projects_dir = projects_dir
        self._lock = Lock()

    def create_project(
        self,
        project_id: str,
        files: list[FileSummary],
        chunks: list[dict],
        topics: list[Topic],
    ) -> dict:
        project = {
            "project_id": project_id,
            "files": [file.model_dump() for file in files],
            "chunks": chunks,
            "topics": [topic.model_dump() for topic in topics],
        }
        self._write_project(project)
        return project

    def get_project(self, project_id: str) -> dict | None:
        path = self._project_path(project_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_project(self, project: dict) -> None:
        with self._lock:
            self._project_path(project["project_id"]).write_text(
                json.dumps(project, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    def _project_path(self, project_id: str) -> Path:
        return self.projects_dir / f"{project_id}.json"


study_store = StudyStore(settings.projects_dir)

