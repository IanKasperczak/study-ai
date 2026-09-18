import pytest

from app.services.quiz_store import QuizStore


@pytest.fixture
def store(tmp_path):
    return QuizStore(tmp_path / "test.db")


def test_record_attempt_returns_the_saved_row(store):
    attempt = store.record_attempt(
        user_id="u1", project_id="p1", subtema_id="t1", score=4, total_questions=5
    )
    assert attempt["user_id"] == "u1"
    assert attempt["project_id"] == "p1"
    assert attempt["subtema_id"] == "t1"
    assert attempt["score"] == 4
    assert attempt["total_questions"] == 5
    assert attempt["id"] is not None
    assert attempt["created_at"]


def test_list_attempts_only_returns_that_users_and_projects_rows(store):
    store.record_attempt(user_id="u1", project_id="p1", subtema_id="t1", score=3, total_questions=5)
    store.record_attempt(user_id="u2", project_id="p1", subtema_id="t1", score=5, total_questions=5)
    store.record_attempt(user_id="u1", project_id="p2", subtema_id="t2", score=2, total_questions=5)

    attempts = store.list_attempts("u1", "p1")
    assert len(attempts) == 1
    assert attempts[0]["user_id"] == "u1"
    assert attempts[0]["project_id"] == "p1"


def test_list_attempts_orders_most_recent_first(store):
    first = store.record_attempt(user_id="u1", project_id="p1", subtema_id="t1", score=1, total_questions=5)
    second = store.record_attempt(user_id="u1", project_id="p1", subtema_id="t2", score=2, total_questions=5)

    attempts = store.list_attempts("u1", "p1")
    assert attempts[0]["id"] == second["id"]
    assert attempts[1]["id"] == first["id"]


def test_list_attempts_respects_limit(store):
    for i in range(5):
        store.record_attempt(user_id="u1", project_id="p1", subtema_id=f"t{i}", score=1, total_questions=5)

    assert len(store.list_attempts("u1", "p1", limit=2)) == 2


def test_delete_attempt_removes_only_the_owners_row(store):
    attempt = store.record_attempt(user_id="u1", project_id="p1", subtema_id="t1", score=1, total_questions=5)

    assert store.delete_attempt("u2", attempt["id"]) is False  # wrong owner, no-op
    assert len(store.list_attempts("u1", "p1")) == 1

    assert store.delete_attempt("u1", attempt["id"]) is True
    assert store.list_attempts("u1", "p1") == []


def test_delete_attempt_returns_false_for_unknown_id(store):
    assert store.delete_attempt("u1", 999) is False


def test_record_attempt_persists_questions_and_answers_for_later_review(store):
    questions = [
        {"question": "2+2?", "options": ["3", "4"], "correct_index": 1, "explanation": "Suma basica."}
    ]
    attempt = store.record_attempt(
        user_id="u1",
        project_id="p1",
        subtema_id="t1",
        score=1,
        total_questions=1,
        questions=questions,
        answers=[1],
    )
    assert attempt["questions"] == questions
    assert attempt["answers"] == [1]

    fetched = store.list_attempts("u1", "p1")[0]
    assert fetched["questions"] == questions
    assert fetched["answers"] == [1]


def test_record_attempt_defaults_questions_and_answers_to_empty(store):
    attempt = store.record_attempt(user_id="u1", project_id="p1", subtema_id="t1", score=1, total_questions=5)
    assert attempt["questions"] == []
    assert attempt["answers"] == []
