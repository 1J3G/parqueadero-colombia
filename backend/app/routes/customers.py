from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.auth import get_current_user
from app.database import transaction

router = APIRouter(prefix="/api/customers", tags=["customers"])


class CustomerCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_type: str = Field(pattern="^(CC|CE|NIT)$")
    document: str = Field(min_length=1, max_length=30)
    full_name: str = Field(min_length=1, max_length=160)


@router.post("", status_code=201)
def create_customer(payload: CustomerCreate, _user: dict = Depends(get_current_user)) -> dict:
    document = payload.document.strip()
    full_name = payload.full_name.strip()
    if not document or not full_name:
        raise HTTPException(status_code=400, detail="Documento y nombre del cliente son obligatorios.")
    with transaction() as cursor:
        cursor.execute(
            """
            INSERT INTO customers (document_type, document, full_name)
            VALUES (%s, %s, %s)
            """,
            (payload.document_type, document, full_name),
        )
        customer_id = cursor.lastrowid
    return {
        "id": customer_id,
        "document_type": payload.document_type,
        "document": document,
        "full_name": full_name,
    }


@router.get("")
def list_customers(_user: dict = Depends(get_current_user)) -> list[dict]:
    with transaction() as cursor:
        cursor.execute(
            """
            SELECT id, document_type, document, full_name
            FROM customers
            ORDER BY full_name, id
            """
        )
        return cursor.fetchall()
