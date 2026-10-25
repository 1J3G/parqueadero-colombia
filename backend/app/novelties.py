from typing import Any


def record_novelty(
    cursor: Any,
    transit_id: int,
    novelty_type: str,
    description: str,
    severity: str | None,
    recorded_by: int,
    damage_type: str | None = None,
) -> None:
    cursor.execute(
        """
        INSERT INTO novelties
          (transit_id, novelty_type, damage_type, description, severity, recorded_by)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (transit_id, novelty_type, damage_type, description, severity, recorded_by),
    )
