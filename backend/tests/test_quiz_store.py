import pytest

from app.services.quiz_store import QuizStore


@pytest.fixture
def store(tmp_path):
    return QuizStore(tmp_path / "test.db")


def test_record_attempt_returns_the_saved_row(store):
    attempt = store.record_attempt(
        user_id="u1", subtema_id="t1", score=4, total_questions=5
    )
    assert attempt["user_id"] == "u1"
    assert attempt["subtema_id"] == "t1"
    assert attempt["score"] == 4
    assert attempt["total_questions"] == 5
    assert attempt["id"] is not None
    assert attempt["created_at"]


def test_list_attempts_only_returns_that_users_rows(store):
    store.record_attempt(user_id="u1", subtema_id="t1", score=3, total_questions=5)
    store.record_attempt(user_id="u2", subtema_id="t1", score=5, total_questions=5)
    store.record_attempt(user_id="u1", subtema_id="t2", score=2, total_questions=5)

    attempts = store.list_attempts("u1")
    assert len(attempts) == 2
    assert all(attempt["user_id"] == "u1" for attempt in attempts)


def test_list_attempts_orders_most_recent_first(store):
    first = store.record_attempt(user_id="u1", subtema_id="t1", score=1, total_questions=5)
    second = store.record_attempt(user_id="u1", subtema_id="t2", score=2, total_questions=5)

    attempts = store.list_attempts("u1")
    assert attempts[0]["id"] == second["id"]
    assert attempts[1]["id"] == first["id"]


def test_list_attempts_respects_limit(store):
    for i in range(5):
        store.record_attempt(user_id="u1", subtema_id=f"t{i}", score=1, total_questions=5)

    assert len(store.list_attempts("u1", limit=2)) == 2
