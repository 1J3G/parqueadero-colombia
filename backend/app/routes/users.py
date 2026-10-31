from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.auth import hash_password, require_administrator
from app.database import transaction

router = APIRouter(prefix="/api/users", tags=["users"])


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document: str = Field(min_length=1, max_length=30)
    password: str = Field(min_length=1, max_length=256)
    role: Literal["Operario", "Administrador"]


@router.get("")
def list_users(_administrator: dict = Depends(require_administrator)) -> list[dict]:
    with transaction() as cursor:
        cursor.execute("SELECT id, document, role, created_at FROM users ORDER BY document")
        return cursor.fetchall()


@router.post("", status_code=201)
def create_user(
    payload: UserCreate,
    _administrator: dict = Depends(require_administrator),
) -> dict:
    document = payload.document.strip()
    if not document:
        raise HTTPException(status_code=400, detail="El documento es obligatorio.")
    password_hash = hash_password(payload.password)
    with transaction() as cursor:
        cursor.execute(
            "INSERT INTO users (document, password_hash, role) VALUES (%s, %s, %s)",
            (document, password_hash, payload.role),
        )
        user_id = cursor.lastrowid
    return {"id": user_id, "document": document, "role": payload.role}
