from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.auth import get_current_user
from app.cash import find_open_cash
from app.database import transaction

router = APIRouter(prefix="/api/cash", tags=["cash"])


class CashOpeningRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_amount: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


@router.post("/open", status_code=201)
def open_cash(payload: CashOpeningRequest, user: dict = Depends(get_current_user)) -> dict:
    with transaction() as cursor:
        cursor.execute("SELECT id FROM users WHERE id = %s FOR UPDATE", (user["id"],))
        if cursor.fetchone() is None:
            raise HTTPException(status_code=401, detail="La sesión no está activa.")
        if find_open_cash(cursor, user["id"], lock=True):
            raise HTTPException(status_code=409, detail="Ya tiene una caja abierta.")
        cursor.execute(
            "INSERT INTO cash_openings (user_id, base_amount) VALUES (%s, %s)",
            (user["id"], payload.base_amount),
        )
        cash_id = cursor.lastrowid
    return {"id": cash_id, "user_id": user["id"], "base_amount": payload.base_amount}


@router.get("/current")
def current_cash(user: dict = Depends(get_current_user)) -> dict | None:
    with transaction() as cursor:
        return find_open_cash(cursor, user["id"])


@router.get("/open")
def list_open_cash(user: dict = Depends(get_current_user)) -> list[dict]:
    if user["role"] != "Administrador":
        raise HTTPException(status_code=403, detail="Solo un Administrador puede consultar todas las cajas abiertas.")
    with transaction() as cursor:
        cursor.execute(
            """
            SELECT c.id, c.user_id, u.document AS user_document, c.base_amount, c.opened_at
            FROM cash_openings c
            JOIN users u ON u.id = c.user_id
            WHERE c.closed_at IS NULL
            ORDER BY c.opened_at, c.id
            """
        )
        return cursor.fetchall()


@router.post("/{cash_id}/close")
def close_cash(cash_id: int, user: dict = Depends(get_current_user)) -> dict:
    with transaction() as cursor:
        cursor.execute(
            "SELECT id, user_id, closed_at FROM cash_openings WHERE id = %s FOR UPDATE",
            (cash_id,),
        )
        cash = cursor.fetchone()
        if cash is None:
            raise HTTPException(status_code=404, detail="No se encontró la caja.")
        if cash["closed_at"] is not None:
            raise HTTPException(status_code=409, detail="La caja ya está cerrada.")
        if cash["user_id"] != user["id"] and user["role"] != "Administrador":
            raise HTTPException(status_code=403, detail="Solo el titular o un Administrador puede cerrar esta caja.")
        cursor.execute(
            """
            UPDATE cash_openings
            SET closed_at = CURRENT_TIMESTAMP(6)
            WHERE id = %s AND closed_at IS NULL
            """,
            (cash_id,),
        )
        if cursor.rowcount != 1:
            raise HTTPException(status_code=409, detail="La caja dejó de estar abierta.")
        cursor.execute("SELECT closed_at FROM cash_openings WHERE id = %s", (cash_id,))
        closed_at = cursor.fetchone()["closed_at"]
    return {"id": cash_id, "closed_at": closed_at, "status": "Cerrada"}
