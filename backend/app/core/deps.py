"""Shared FastAPI dependencies.

Anonymous per-device identity: the frontend generates a UUID once (stored in
localStorage) and sends it as X-User-Id on every request. There is no login
-- this is a conscious choice so anyone can try the demo without signing up,
while still letting per-device data (like quiz history) persist across
visits. Nothing here proves the header is trustworthy; it is an identifier,
not an authentication credential.
"""
import uuid
from typing import Annotated

from fastapi import Header, HTTPException


def get_user_id(x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None) -> str:
    if not x_user_id:
        raise HTTPException(status_code=400, detail="Falta el header X-User-Id.")
    try:
        uuid.UUID(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="X-User-Id debe ser un UUID valido.")
    return x_user_id
