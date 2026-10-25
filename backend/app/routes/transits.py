from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.auth import get_current_user, verify_password
from app.cash import require_open_cash
from app.contracts import mark_expired_contracts
from app.database import transaction
from app.domain import compatible_cell, require_entry_permission
from app.novelties import record_novelty

router = APIRouter(prefix="/api/transits", tags=["transits"])


class ExceptionalAuthorization(BaseModel):
    model_config = ConfigDict(extra="forbid")

    administrator_document: str = Field(min_length=1, max_length=30)
    administrator_password: str = Field(min_length=1, max_length=256)
    novelty: str = Field(min_length=1, max_length=1000)


class PhysicalNovelty(BaseModel):
    model_config = ConfigDict(extra="forbid")

    damage_type: Literal["Golpe", "Rayón", "Falla"]
    description: str = Field(min_length=1, max_length=1000)
    severity: Literal["Leve", "Moderada", "Grave"]


class EntryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_id: int = Field(gt=0)
    cell_id: int = Field(gt=0)
    exceptional_authorization: ExceptionalAuthorization | None = None
    physical_novelties: list[PhysicalNovelty] = Field(default_factory=list)


class ExitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_id: int = Field(gt=0)


def verify_exceptional_administrator(cursor, authorization: ExceptionalAuthorization) -> int:
    cursor.execute(
        "SELECT id, password_hash FROM users WHERE document = %s AND role = 'Administrador'",
        (authorization.administrator_document.strip(),),
    )
    administrator = cursor.fetchone()
    if administrator is None or not verify_password(authorization.administrator_password, administrator["password_hash"]):
        raise HTTPException(status_code=403, detail="La autorización administrativa no es válida.")
    return administrator["id"]


@router.post("/entry", status_code=201)
def register_entry(payload: EntryRequest, operator: dict = Depends(get_current_user)) -> dict:
    with transaction() as cursor:
        if operator["role"] == "Operario":
            require_open_cash(cursor, operator["id"])

        mark_expired_contracts(cursor)
        cursor.execute(
            """
            SELECT c.id AS contract_id, c.status, c.expires_on, v.id AS vehicle_id,
                   v.vehicle_type
            FROM contracts c
            JOIN vehicles v ON v.id = c.vehicle_id
            WHERE c.id = %s
            FOR UPDATE
            """,
            (payload.contract_id,),
        )
        contract = cursor.fetchone()
        if contract is None:
            raise HTTPException(status_code=404, detail="No se encontró el contrato.")

        cursor.execute("SELECT CURRENT_DATE() AS server_date")
        server_date: date = cursor.fetchone()["server_date"]
        exceptional = payload.exceptional_authorization is not None
        require_entry_permission(contract["status"], contract["expires_on"], server_date, exceptional)

        admin_id = None
        if exceptional:
            if not payload.exceptional_authorization.novelty.strip():
                raise HTTPException(status_code=400, detail="La novedad de acceso excepcional es obligatoria.")
            admin_id = verify_exceptional_administrator(cursor, payload.exceptional_authorization)
        if any(not novelty.description.strip() for novelty in payload.physical_novelties):
            raise HTTPException(status_code=400, detail="La descripción de cada daño preexistente es obligatoria.")

        cursor.execute(
            """
            SELECT direction, cell_id
            FROM transits
            WHERE vehicle_id = %s
            ORDER BY occurred_at DESC, id DESC
            LIMIT 1
            FOR UPDATE
            """,
            (contract["vehicle_id"],),
        )
        latest_transit = cursor.fetchone()
        if latest_transit is not None and latest_transit["direction"] == "Entrada":
            raise HTTPException(status_code=409, detail="El vehículo ya está dentro del parqueadero.")

        cursor.execute(
            "SELECT id, category, status FROM cells WHERE id = %s FOR UPDATE",
            (payload.cell_id,),
        )
        cell = cursor.fetchone()
        if cell is None:
            raise HTTPException(status_code=404, detail="No se encontró la celda.")
        if not compatible_cell(contract["vehicle_type"], cell["category"]):
            raise HTTPException(status_code=409, detail="La celda no es compatible con el tipo de vehículo.")
        if cell["status"] != "Disponible":
            raise HTTPException(status_code=409, detail="La celda se encuentra ocupada.")

        cursor.execute(
            "UPDATE cells SET status = 'Ocupada' WHERE id = %s AND status = 'Disponible'",
            (payload.cell_id,),
        )
        if cursor.rowcount != 1:
            raise HTTPException(status_code=409, detail="La celda dejó de estar disponible.")

        cursor.execute(
            """
            INSERT INTO transits (vehicle_id, contract_id, cell_id, operator_id, direction)
            VALUES (%s, %s, %s, %s, 'Entrada')
            """,
            (contract["vehicle_id"], contract["contract_id"], payload.cell_id, operator["id"]),
        )
        transit_id = cursor.lastrowid
        if payload.exceptional_authorization is not None:
            record_novelty(
                cursor,
                transit_id,
                "Acceso excepcional",
                payload.exceptional_authorization.novelty.strip(),
                None,
                admin_id,
            )
        for novelty in payload.physical_novelties:
            record_novelty(
                cursor,
                transit_id,
                "Daño físico",
                novelty.description.strip(),
                novelty.severity,
                operator["id"],
                novelty.damage_type,
            )

    return {
        "id": transit_id,
        "contract_id": payload.contract_id,
        "cell_id": payload.cell_id,
        "direction": "Entrada",
        "message": "Entrada registrada.",
    }


@router.post("/exit", status_code=201)
def register_exit(payload: ExitRequest, operator: dict = Depends(get_current_user)) -> dict:
    with transaction() as cursor:
        if operator["role"] == "Operario":
            require_open_cash(cursor, operator["id"])

        cursor.execute(
            """
            SELECT c.id AS contract_id, v.id AS vehicle_id
            FROM contracts c
            JOIN vehicles v ON v.id = c.vehicle_id
            WHERE c.id = %s
            FOR UPDATE
            """,
            (payload.contract_id,),
        )
        contract = cursor.fetchone()
        if contract is None:
            raise HTTPException(status_code=404, detail="No se encontró el contrato.")

        cursor.execute(
            """
            SELECT id, cell_id, direction
            FROM transits
            WHERE vehicle_id = %s
            ORDER BY occurred_at DESC, id DESC
            LIMIT 1
            FOR UPDATE
            """,
            (contract["vehicle_id"],),
        )
        entry = cursor.fetchone()
        if entry is None or entry["direction"] != "Entrada":
            raise HTTPException(status_code=409, detail="El vehículo está fuera del parqueadero.")

        cursor.execute(
            "UPDATE cells SET status = 'Disponible' WHERE id = %s AND status = 'Ocupada'",
            (entry["cell_id"],),
        )
        if cursor.rowcount != 1:
            raise HTTPException(status_code=409, detail="No fue posible liberar la celda asociada.")
        cursor.execute(
            """
            INSERT INTO transits (vehicle_id, contract_id, cell_id, operator_id, direction)
            VALUES (%s, %s, %s, %s, 'Salida')
            """,
            (contract["vehicle_id"], contract["contract_id"], entry["cell_id"], operator["id"]),
        )
        transit_id = cursor.lastrowid

    return {
        "id": transit_id,
        "contract_id": payload.contract_id,
        "cell_id": entry["cell_id"],
        "direction": "Salida",
        "message": "Salida registrada y celda liberada.",
    }
