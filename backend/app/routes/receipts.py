from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user
from app.database import transaction

router = APIRouter(prefix="/api/receipts", tags=["receipts"])


@router.get("/{payment_id}")
def get_receipt(payment_id: int, _user: dict = Depends(get_current_user)) -> dict:
    with transaction() as cursor:
        cursor.execute(
            """
            SELECT id, payment_id, consecutive_number, customer_document_type,
                   customer_document, customer_full_name, net_amount, tax_amount,
                   total_amount, issued_at
            FROM receipts
            WHERE payment_id = %s
            """,
            (payment_id,),
        )
        receipt = cursor.fetchone()
    if receipt is None:
        raise HTTPException(status_code=404, detail="No se encontró el comprobante.")
    return receipt
