"""SQLite-backed store for quiz attempts.

Everything else in this app is JSON-on-disk (see study_store.py); quiz
attempts get a real table because they're naturally tabular records queried
by user_id, and SQLite needs no extra infrastructure to keep that MVP-simple
property. Keyed by the anonymous per-device user_id from X-User-Id (see
app/core/deps.py) AND project_id, so switching documents/projects doesn't mix
quiz history or retakes across unrelated material.
"""
import json
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
                    project_id TEXT NOT NULL,
                    subtema_id TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    total_questions INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_quiz_attempts_user_project "
                "ON quiz_attempts(user_id, project_id)"
            )
            # Added later so a graded quiz can be reopened for review without
            # retaking it. ALTER TABLE (not a table rebuild) so it's safe to
            # run against a database that already has rows from before these
            # columns existed -- those old rows just come back with "[]".
            existing_columns = {
                row["name"] for row in connection.execute("PRAGMA table_info(quiz_attempts)")
            }
            if "questions_json" not in existing_columns:
                connection.execute(
                    "ALTER TABLE quiz_attempts ADD COLUMN questions_json TEXT NOT NULL DEFAULT '[]'"
                )
            if "answers_json" not in existing_columns:
                connection.execute(
                    "ALTER TABLE quiz_attempts ADD COLUMN answers_json TEXT NOT NULL DEFAULT '[]'"
                )

    def record_attempt(
        self,
        user_id: str,
        project_id: str,
        subtema_id: str,
        score: int,
        total_questions: int,
        questions: list[dict] | None = None,
        answers: list[int] | None = None,
    ) -> dict:
        questions = questions or []
        answers = answers or []
        created_at = datetime.now(timezone.utc).isoformat()
        questions_json = json.dumps(questions)
        answers_json = json.dumps(answers)
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO quiz_attempts
                    (user_id, project_id, subtema_id, score, total_questions, created_at,
                     questions_json, answers_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    project_id,
                    subtema_id,
                    score,
                    total_questions,
                    created_at,
                    questions_json,
                    answers_json,
                ),
            )
            return {
                "id": cursor.lastrowid,
                "user_id": user_id,
                "project_id": project_id,
                "subtema_id": subtema_id,
                "score": score,
                "total_questions": total_questions,
                "created_at": created_at,
                "questions": questions,
                "answers": answers,
            }

    def list_attempts(self, user_id: str, project_id: str, limit: int = 50) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, user_id, project_id, subtema_id, score, total_questions, created_at,
                       questions_json, answers_json
                FROM quiz_attempts
                WHERE user_id = ? AND project_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (user_id, project_id, limit),
            ).fetchall()
            return [self._row_to_dict(row) for row in rows]

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        attempt = dict(row)
        attempt["questions"] = json.loads(attempt.pop("questions_json"))
        attempt["answers"] = json.loads(attempt.pop("answers_json"))
        return attempt

    def delete_attempt(self, user_id: str, attempt_id: int) -> bool:
        """Delete an attempt if it belongs to user_id. Returns whether a row
        was actually removed, so the route can 404 on a foreign/missing id."""
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM quiz_attempts WHERE id = ? AND user_id = ?",
                (attempt_id, user_id),
            )
            return cursor.rowcount > 0


quiz_store = QuizStore(settings.db_path)
