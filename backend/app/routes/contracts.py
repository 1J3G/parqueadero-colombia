from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.auth import get_current_user, require_administrator
from app.contracts import cancel_contract, mark_expired_contracts
from app.database import transaction
from app.vehicles import validate_plate

router = APIRouter(prefix="/api/contracts", tags=["contracts"])


class ContractCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_id: int = Field(gt=0)
    plate: str = Field(min_length=6, max_length=6)
    vehicle_type: str = Field(pattern="^(Carro|Moto|Camioneta)$")


class PlateChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plate: str = Field(min_length=6, max_length=6)


class ContractCancellation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    justification: str = Field(min_length=1, max_length=1000)


@router.post("", status_code=201)
def create_contract(payload: ContractCreate, _user: dict = Depends(get_current_user)) -> dict:
    plate = validate_plate(payload.plate, payload.vehicle_type)
    with transaction() as cursor:
        cursor.execute("SELECT id FROM customers WHERE id = %s", (payload.customer_id,))
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="No se encontró el cliente.")
        cursor.execute("SELECT id, vehicle_type FROM vehicles WHERE plate = %s", (plate,))
        vehicle = cursor.fetchone()
        if vehicle is None:
            cursor.execute(
                "INSERT INTO vehicles (plate, vehicle_type) VALUES (%s, %s)",
                (plate, payload.vehicle_type),
            )
            vehicle_id = cursor.lastrowid
        else:
            if vehicle["vehicle_type"] != payload.vehicle_type:
                raise HTTPException(status_code=409, detail="La placa ya está registrada con otro tipo de vehículo.")
            vehicle_id = vehicle["id"]
        cursor.execute(
            """
            INSERT INTO contracts (customer_id, vehicle_id)
            VALUES (%s, %s)
            """,
            (payload.customer_id, vehicle_id),
        )
        contract_id = cursor.lastrowid
    return {
        "id": contract_id,
        "customer_id": payload.customer_id,
        "vehicle_id": vehicle_id,
        "plate": plate,
        "vehicle_type": payload.vehicle_type,
        "status": "Pendiente de Pago",
        "expires_on": None,
    }


@router.get("")
def list_contracts(_user: dict = Depends(get_current_user)) -> list[dict]:
    with transaction() as cursor:
        mark_expired_contracts(cursor)
        cursor.execute(
            """
            SELECT c.id, c.customer_id, c.vehicle_id, v.plate, v.vehicle_type,
                   c.status, c.expires_on, cu.document AS customer_document,
                   cu.full_name AS customer_full_name
            FROM contracts c
            JOIN vehicles v ON v.id = c.vehicle_id
            JOIN customers cu ON cu.id = c.customer_id
            ORDER BY c.created_at DESC, c.id DESC
            """
        )
        return cursor.fetchall()


@router.post("/{contract_id}/cancel")
def cancel_contract_route(
    contract_id: int,
    payload: ContractCancellation,
    administrator: dict = Depends(require_administrator),
) -> dict:
    with transaction() as cursor:
        result = cancel_contract(cursor, contract_id, administrator["id"], payload.justification)
    return result


@router.patch("/{contract_id}/plate")
def change_contract_plate(
    contract_id: int,
    payload: PlateChange,
    administrator: dict = Depends(require_administrator),
) -> dict:
    with transaction() as cursor:
        cursor.execute(
            """
            SELECT c.id, c.vehicle_id, v.vehicle_type, v.plate
            FROM contracts c
            JOIN vehicles v ON v.id = c.vehicle_id
            WHERE c.id = %s
            FOR UPDATE
            """,
            (contract_id,),
        )
        contract = cursor.fetchone()
        if contract is None:
            raise HTTPException(status_code=404, detail="No se encontró el contrato.")
        plate = validate_plate(payload.plate, contract["vehicle_type"])
        if plate == contract["plate"]:
            return {
                "contract_id": contract_id,
                "plate": plate,
                "authorized_by": administrator["document"],
            }
        cursor.execute(
            """
            SELECT direction
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
            raise HTTPException(status_code=409, detail="No se puede cambiar la placa mientras el vehículo está dentro.")
        cursor.execute("SELECT id, vehicle_type FROM vehicles WHERE plate = %s FOR UPDATE", (plate,))
        vehicle = cursor.fetchone()
        if vehicle is not None and vehicle["vehicle_type"] != contract["vehicle_type"]:
            raise HTTPException(status_code=409, detail="La placa ya está registrada con otro tipo de vehículo.")
        if vehicle is not None:
            cursor.execute(
                """
                SELECT direction
                FROM transits
                WHERE vehicle_id = %s
                ORDER BY occurred_at DESC, id DESC
                LIMIT 1
                FOR UPDATE
                """,
                (vehicle["id"],),
            )
            latest_transit = cursor.fetchone()
            if latest_transit is not None and latest_transit["direction"] == "Entrada":
                raise HTTPException(status_code=409, detail="La nueva placa pertenece a un vehículo que está dentro.")
        if vehicle is None:
            cursor.execute(
                "INSERT INTO vehicles (plate, vehicle_type) VALUES (%s, %s)",
                (plate, contract["vehicle_type"]),
            )
            vehicle_id = cursor.lastrowid
        else:
            vehicle_id = vehicle["id"]
        cursor.execute(
            "UPDATE contracts SET vehicle_id = %s WHERE id = %s",
            (vehicle_id, contract_id),
        )
    return {
        "contract_id": contract_id,
        "plate": plate,
        "authorized_by": administrator["document"],
    }
