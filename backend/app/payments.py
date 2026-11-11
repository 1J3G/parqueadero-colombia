from datetime import date, timedelta
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
        SELECT c.id, c.status, c.starts_on, c.expires_on, c.customer_id, c.vehicle_id
        FROM contracts c
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
    cursor.execute("SELECT id FROM vehicles WHERE id = %s FOR UPDATE", (contract["vehicle_id"],))
    if cursor.fetchone() is None:
        raise RuntimeError("The vehicle linked to the contract is missing.")
    if net_amount <= 0:
        raise HTTPException(status_code=400, detail="El valor neto debe ser mayor que cero.")
    if paid_months < 1:
        raise HTTPException(status_code=400, detail="La cantidad de meses pagados debe ser mayor que cero.")
    if payment_method == "Transferencia Bancaria" and not (reference_code and reference_code.strip()):
        raise HTTPException(status_code=400, detail="La transferencia requiere código o número de referencia.")

    cursor.execute("SELECT CURRENT_DATE() AS payment_date")
    payment_date: date = cursor.fetchone()["payment_date"]
    cursor.execute(
        """
        SELECT MAX(expires_on) AS latest_expiration
        FROM contracts
        WHERE customer_id = %s
          AND vehicle_id = %s
          AND status = 'Activo'
          AND expires_on >= %s
        """,
        (contract["customer_id"], contract["vehicle_id"], payment_date),
    )
    latest_expiration = cursor.fetchone()["latest_expiration"]
    cursor.execute(
        "SELECT document_type, document, full_name FROM customers WHERE id = %s",
        (contract["customer_id"],),
    )
    customer = cursor.fetchone()
    if customer is None:
        raise RuntimeError("The customer linked to the contract is missing.")
    contract_has_unexpired_period = (
        contract["status"] == "Activo"
        and contract["expires_on"] is not None
        and contract["expires_on"] >= payment_date
    )
    if contract_has_unexpired_period:
        starts_on = contract["starts_on"] or payment_date
    elif latest_expiration is not None:
        starts_on = latest_expiration + timedelta(days=1)
    else:
        starts_on = payment_date
    expires_on = renewed_expiration(contract["status"], latest_expiration, paid_months, payment_date)
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
        "UPDATE contracts SET status = 'Activo', starts_on = %s, expires_on = %s WHERE id = %s",
        (starts_on, expires_on, contract_id),
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
            customer["document_type"],
            customer["document"],
            customer["full_name"],
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
        "starts_on": starts_on,
        "customer_document_type": customer["document_type"],
        "customer_document": customer["document"],
        "customer_full_name": customer["full_name"],
        "net_amount": net_amount,
        "tax_amount": tax_amount,
        "total_amount": total_amount,
        "expires_on": expires_on,
    }
