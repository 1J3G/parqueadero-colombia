from fastapi import APIRouter, Depends, Query

from app.auth import get_current_user
from app.database import transaction
from app.domain import compatible_cell

router = APIRouter(prefix="/api/cells", tags=["cells"])


@router.get("")
def list_cells(
    vehicle_type: str | None = Query(default=None, pattern="^(Carro|Moto|Camioneta)$"),
    _user: dict = Depends(get_current_user),
) -> list[dict]:
    with transaction() as cursor:
        cursor.execute("SELECT id, label, category, status FROM cells ORDER BY label")
        cells = cursor.fetchall()
    if vehicle_type is None:
        return cells
    return [
        cell
        for cell in cells
        if cell["status"] == "Disponible" and compatible_cell(vehicle_type, cell["category"])
    ]
