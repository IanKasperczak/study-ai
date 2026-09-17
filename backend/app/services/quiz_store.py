"""SQLite-backed store for quiz attempts.

Everything else in this app is JSON-on-disk (see study_store.py); quiz
attempts get a real table because they're naturally tabular records queried
by user_id, and SQLite needs no extra infrastructure to keep that MVP-simple
property. Keyed by the anonymous per-device user_id from X-User-Id (see
app/core/deps.py), not by project, so a device's quiz history survives
across projects.
"""
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import get_settings

settings = get_settings()


class QuizStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.db_path))
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS quiz_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    subtema_id TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    total_questions INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_quiz_attempts_user_id ON quiz_attempts(user_id)"
            )

    def record_attempt(
        self, user_id: str, subtema_id: str, score: int, total_questions: int
    ) -> dict:
        created_at = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO quiz_attempts (user_id, subtema_id, score, total_questions, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, subtema_id, score, total_questions, created_at),
            )
            return {
                "id": cursor.lastrowid,
                "user_id": user_id,
                "subtema_id": subtema_id,
                "score": score,
                "total_questions": total_questions,
                "created_at": created_at,
            }

    def list_attempts(self, user_id: str, limit: int = 50) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, user_id, subtema_id, score, total_questions, created_at
                FROM quiz_attempts
                WHERE user_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
            return [dict(row) for row in rows]


quiz_store = QuizStore(settings.db_path)
