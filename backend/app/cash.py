from typing import Any

from fastapi import HTTPException


def find_open_cash(cursor: Any, user_id: int, lock: bool = False) -> dict[str, Any] | None:
    lock_clause = " FOR UPDATE" if lock else ""
    cursor.execute(
        f"""
        SELECT id, user_id, base_amount, opened_at
        FROM cash_openings
        WHERE user_id = %s AND closed_at IS NULL
        ORDER BY id DESC
        LIMIT 1
        {lock_clause}
        """,
        (user_id,),
    )
    return cursor.fetchone()


def require_open_cash(cursor: Any, user_id: int) -> dict[str, Any]:
    cash = find_open_cash(cursor, user_id, lock=True)
    if cash is None:
        raise HTTPException(status_code=409, detail="Abra una caja a su nombre antes de procesar esta transacción.")
    return cash
