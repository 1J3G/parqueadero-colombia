from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.auth import get_current_user, verify_password
from app.cash import require_open_cash
from app.database import transaction
from app.payments import register_payment

router = APIRouter(prefix="/api/payments", tags=["payments"])


class PaymentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_id: int = Field(gt=0)
    paid_months: int = Field(ge=1)
    net_amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    payment_method: Literal["Efectivo", "Transferencia Bancaria", "Tarjeta Crédito/Débito"]
    reference_code: str | None = Field(default=None, max_length=120)


class PaymentVoidRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    administrator_password: str = Field(min_length=1, max_length=256)
    justification: str = Field(min_length=1, max_length=1000)


@router.post("", status_code=201)
def create_payment(payload: PaymentRequest, user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "Operario":
        raise HTTPException(status_code=403, detail="El cobro de mensualidades debe realizarlo un Operario.")
    with transaction() as cursor:
        cash = require_open_cash(cursor, user["id"])
        result = register_payment(
            cursor,
            payload.contract_id,
            cash,
            payload.paid_months,
            payload.net_amount,
            payload.payment_method,
            payload.reference_code,
        )
    return result


@router.post("/{payment_id}/void")
def void_payment(
    payment_id: int,
    payload: PaymentVoidRequest,
    administrator: dict = Depends(get_current_user),
) -> dict:
    if administrator["role"] != "Administrador":
        raise HTTPException(status_code=403, detail="Solo un Administrador puede anular pagos.")
    if not payload.justification.strip():
        raise HTTPException(status_code=400, detail="La justificación es obligatoria.")
    with transaction() as cursor:
        cursor.execute(
            "SELECT password_hash FROM users WHERE id = %s AND role = 'Administrador'",
            (administrator["id"],),
        )
        user = cursor.fetchone()
        if user is None or not verify_password(payload.administrator_password, user["password_hash"]):
            raise HTTPException(status_code=403, detail="Las credenciales de confirmación no son válidas.")
        cursor.execute("SELECT id, status FROM payments WHERE id = %s FOR UPDATE", (payment_id,))
        payment = cursor.fetchone()
        if payment is None:
            raise HTTPException(status_code=404, detail="No se encontró el pago.")
        if payment["status"] == "Anulado":
            raise HTTPException(status_code=409, detail="El pago ya fue anulado.")
        cursor.execute("UPDATE payments SET status = 'Anulado' WHERE id = %s", (payment_id,))
        cursor.execute(
            """
            INSERT INTO payment_audit (payment_id, administrator_id, justification)
            VALUES (%s, %s, %s)
            """,
            (payment_id, administrator["id"], payload.justification.strip()),
        )
    return {"payment_id": payment_id, "status": "Anulado", "message": "La anulación quedó registrada en auditoría."}
