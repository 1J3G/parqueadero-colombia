from typing import Any

from fastapi import HTTPException

from app.domain import renewed_expiration


def mark_expired_contracts(cursor: Any) -> None:
    cursor.execute(
        """
        UPDATE contracts
        SET status = 'Vencido'
        WHERE status = 'Activo'
          AND expires_on IS NOT NULL
          AND expires_on < CURRENT_DATE()
        """
    )


def cancel_contract(cursor: Any, contract_id: int, administrator_id: int, justification: str) -> dict[str, Any]:
    cursor.execute(
        "SELECT id, status FROM contracts WHERE id = %s FOR UPDATE",
        (contract_id,),
    )
    contract = cursor.fetchone()
    if contract is None:
        raise HTTPException(status_code=404, detail="No se encontró el contrato.")
    if contract["status"] == "Cancelado":
        raise HTTPException(status_code=409, detail="El contrato ya está Cancelado.")
    normalized_justification = justification.strip()
    if not normalized_justification:
        raise HTTPException(status_code=400, detail="La justificación de cancelación es obligatoria.")
    cursor.execute(
        """
        UPDATE contracts
        SET status = 'Cancelado',
            cancelled_by = %s,
            cancellation_justification = %s,
            cancelled_at = CURRENT_TIMESTAMP(6)
        WHERE id = %s AND status <> 'Cancelado'
        """,
        (administrator_id, normalized_justification, contract_id),
    )
    if cursor.rowcount != 1:
        raise HTTPException(status_code=409, detail="El contrato dejó de estar disponible para cancelación.")
    return {"id": contract_id, "status": "Cancelado"}


__all__ = ["cancel_contract", "mark_expired_contracts", "renewed_expiration"]
