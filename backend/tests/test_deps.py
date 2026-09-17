import pytest
from fastapi import HTTPException

from app.core.deps import get_user_id


def test_get_user_id_accepts_valid_uuid():
    valid = "550e8400-e29b-41d4-a716-446655440000"
    assert get_user_id(valid) == valid


def test_get_user_id_rejects_missing_header():
    with pytest.raises(HTTPException) as exc_info:
        get_user_id(None)
    assert exc_info.value.status_code == 400


def test_get_user_id_rejects_empty_header():
    with pytest.raises(HTTPException) as exc_info:
        get_user_id("")
    assert exc_info.value.status_code == 400


def test_get_user_id_rejects_non_uuid_value():
    with pytest.raises(HTTPException) as exc_info:
        get_user_id("not-a-uuid")
    assert exc_info.value.status_code == 400
