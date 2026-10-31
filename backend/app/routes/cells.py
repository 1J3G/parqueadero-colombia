from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict

from app.auth import get_current_user, require_administrator
from app.database import transaction
from app.domain import compatible_cell

router = APIRouter(prefix="/api/cells", tags=["cells"])


class CellStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["Libre", "En mantenimiento"]


@router.get("")
def list_cells(
    vehicle_type: str | None = Query(default=None, pattern="^(Carro|Moto|Camioneta)$"),
    _user: dict = Depends(get_current_user),
) -> list[dict]:
    with transaction() as cursor:
        cursor.execute(
            """
            SELECT c.id, c.label, c.category, c.status,
                   CASE
                     WHEN c.status = 'Ocupado' AND latest.direction = 'Entrada'
                     THEN v.plate
                     ELSE NULL
                   END AS plate
            FROM cells c
            LEFT JOIN transits latest ON latest.id = (
                SELECT t.id
                FROM transits t
                WHERE t.cell_id = c.id
                ORDER BY t.occurred_at DESC, t.id DESC
                LIMIT 1
            )
            LEFT JOIN vehicles v ON v.id = latest.vehicle_id
            ORDER BY c.label
            """
        )
        cells = cursor.fetchall()
    if vehicle_type is None:
        return cells
    return [
        cell
        for cell in cells
        if cell["status"] == "Libre" and compatible_cell(vehicle_type, cell["category"])
    ]


@router.patch("/{cell_id}/status")
def update_cell_status(
    cell_id: int,
    payload: CellStatusUpdate,
    _administrator: dict = Depends(require_administrator),
) -> dict:
    with transaction() as cursor:
        cursor.execute("SELECT status FROM cells WHERE id = %s FOR UPDATE", (cell_id,))
        cell = cursor.fetchone()
        if cell is None:
            raise HTTPException(status_code=404, detail="No se encontró la celda.")
        if cell["status"] == "Ocupado":
            raise HTTPException(
                status_code=409,
                detail="No se puede cambiar el estado de mantenimiento de una celda ocupada.",
            )
        cursor.execute(
            "UPDATE cells SET status = %s WHERE id = %s AND status = %s",
            (payload.status, cell_id, cell["status"]),
        )
    return {"id": cell_id, "status": payload.status}
