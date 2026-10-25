from datetime import date
from decimal import Decimal
from typing import Any

from fastapi import HTTPException

from app.contracts import mark_expired_contracts
from app.domain import calculate_tax, renewed_expiration
from app.receipts import next_receipt_number


def register_payment(
    cursor: Any,
    contract_id: int,
    cash: dict[str, Any],
    paid_months: int,
    net_amount: Decimal,
    payment_method: str,
    reference_code: str | None,
) -> dict[str, Any]:
    mark_expired_contracts(cursor)
    cursor.execute(
        """
        SELECT c.id, c.status, c.expires_on, c.customer_id,
               cu.document_type, cu.document, cu.full_name
        FROM contracts c
        JOIN customers cu ON cu.id = c.customer_id
        WHERE c.id = %s
        FOR UPDATE
        """,
        (contract_id,),
    )
    contract = cursor.fetchone()
    if contract is None:
        raise HTTPException(status_code=404, detail="No se encontró el contrato.")
    if contract["status"] == "Cancelado":
        raise HTTPException(status_code=409, detail="Un contrato Cancelado no se puede reactivar; cree uno nuevo.")
    if net_amount <= 0:
        raise HTTPException(status_code=400, detail="El valor neto debe ser mayor que cero.")
    if paid_months < 1:
        raise HTTPException(status_code=400, detail="La cantidad de meses pagados debe ser mayor que cero.")
    if payment_method == "Transferencia Bancaria" and not (reference_code and reference_code.strip()):
        raise HTTPException(status_code=400, detail="La transferencia requiere código o número de referencia.")

    cursor.execute("SELECT CURRENT_DATE() AS payment_date")
    payment_date: date = cursor.fetchone()["payment_date"]
    expires_on = renewed_expiration(contract["status"], contract["expires_on"], paid_months, payment_date)
    tax_amount = calculate_tax(net_amount)
    total_amount = net_amount + tax_amount
    cursor.execute(
        """
        INSERT INTO payments
          (contract_id, cash_opening_id, operator_id, net_amount, tax_amount, total_amount,
           paid_months, payment_method, reference_code)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            contract_id,
            cash["id"],
            cash["user_id"],
            net_amount,
            tax_amount,
            total_amount,
            paid_months,
            payment_method,
            reference_code.strip() if reference_code else None,
        ),
    )
    payment_id = cursor.lastrowid
    cursor.execute(
        "UPDATE contracts SET status = 'Activo', expires_on = %s WHERE id = %s",
        (expires_on, contract_id),
    )
    receipt_number = next_receipt_number(cursor)
    cursor.execute(
        """
        INSERT INTO receipts
          (payment_id, consecutive_number, customer_document_type, customer_document,
           customer_full_name, net_amount, tax_amount, total_amount)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            payment_id,
            receipt_number,
            contract["document_type"],
            contract["document"],
            contract["full_name"],
            net_amount,
            tax_amount,
            total_amount,
        ),
    )
    return {
        "payment_id": payment_id,
        "contract_id": contract_id,
        "operator_id": cash["user_id"],
        "receipt_number": receipt_number,
        "customer_document_type": contract["document_type"],
        "customer_document": contract["document"],
        "customer_full_name": contract["full_name"],
        "net_amount": net_amount,
        "tax_amount": tax_amount,
        "total_amount": total_amount,
        "expires_on": expires_on,
    }
