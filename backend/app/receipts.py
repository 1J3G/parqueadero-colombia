from typing import Any


def next_receipt_number(cursor: Any) -> int:
    cursor.execute("SELECT last_number FROM receipt_counters WHERE id = 1 FOR UPDATE")
    counter = cursor.fetchone()
    if counter is None:
        raise RuntimeError("Receipt counter row is missing.")
    number = counter["last_number"] + 1
    cursor.execute("UPDATE receipt_counters SET last_number = %s WHERE id = 1", (number,))
    return number
