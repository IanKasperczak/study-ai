import json
import threading
from pathlib import Path

from app.core.config import get_settings

settings = get_settings()


class StudyStore:
    """Persistent JSON-backed store for per-project state.

    A project holds multiple documents, a flat list of topics (with parent_id
    for hierarchy) and internal RAG chunks. Every mutation happens under a lock
    so concurrent requests cannot lose updates.
    """

    def __init__(self, projects_dir: Path) -> None:
        self.projects_dir = Path(projects_dir)
        self._lock = threading.Lock()

    @staticmethod
    def _blank_project(project_id: str) -> dict:
        return {
            "project_id": project_id,
            "documents": [],
            "chunks": [],
            "topics": [],
        }

    def create_project(self, project_id: str) -> dict:
        project = self._blank_project(project_id)
        self._write_project(project)
        return project

    def get_or_create_project(self, project_id: str) -> dict:
        project = self.get_project(project_id)
        if project is None:
            project = self.create_project(project_id)
        return project

    def get_project(self, project_id: str) -> dict | None:
        path = self._project_path(project_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def add_documents(self, project_id: str, documents: list[dict]) -> None:
        if not documents:
            return
        with self._lock:
            project = self.get_project(project_id)
            if project is None:
                raise KeyError(project_id)
            project["documents"].extend(documents)
            self._write_project(project)

    def remove_document(self, project_id: str, document_id: str) -> dict:
        with self._lock:
            project = self.get_project(project_id)
            if project is None:
                raise KeyError(project_id)
            project["documents"] = [
                doc for doc in project["documents"] if doc["id"] != document_id
            ]
            project["chunks"] = [
                chunk for chunk in project["chunks"] if chunk["document_id"] != document_id
            ]
            project["topics"] = [
                topic for topic in project["topics"] if topic["document_id"] != document_id
            ]
            self._write_project(project)
            return project

    def add_topics(self, project_id: str, topics: list[dict]) -> None:
        with self._lock:
            project = self.get_project(project_id)
            if project is None:
                raise KeyError(project_id)
            project["topics"].extend(topics)
            self._write_project(project)

    def remove_topic(self, project_id: str, topic_id: str) -> dict | None:
        with self._lock:
            project = self.get_project(project_id)
            if project is None:
                raise KeyError(project_id)
            before = len(project["topics"])
            project["topics"] = [
                topic for topic in project["topics"]
                if topic["id"] != topic_id and topic["parent_id"] != topic_id
            ]
            if len(project["topics"]) == before:
                return None
            self._write_project(project)
            return project

    def add_chunks(self, project_id: str, chunks: list[dict]) -> None:
        with self._lock:
            project = self.get_project(project_id)
            if project is None:
                raise KeyError(project_id)
            project["chunks"].extend(chunks)
            self._write_project(project)

    def _write_project(self, project: dict) -> None:
        self._project_path(project["project_id"]).write_text(
            json.dumps(project, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _project_path(self, project_id: str) -> Path:
        return self.projects_dir / f"{project_id}.json"


study_store = StudyStore(settings.projects_dir)