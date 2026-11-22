import json
import uuid

from app.auth import hash_password
from app.database import transaction


def create_fixture() -> dict[str, str | int]:
    suffix = uuid.uuid4().hex[:12].upper()
    operator_document = f"E2EOP{suffix}"
    operator_password = f"E2E-{uuid.uuid4().hex}!"
    customer_document = f"E2ECC{suffix}"
    plate = _unique_car_plate()

    with transaction() as cursor:
        cursor.execute("SELECT DATABASE() AS database_name")
        database_name = cursor.fetchone()["database_name"]
        if not database_name.endswith("_test"):
            raise RuntimeError("Browser E2E fixtures require a database ending with '_test'.")

        cursor.execute(
            """
            INSERT INTO users (document, password_hash, role)
            VALUES (%s, %s, 'Operario')
            """,
            (operator_document, hash_password(operator_password)),
        )
        cursor.execute(
            """
            INSERT INTO customers (document_type, document, full_name)
            VALUES ('CC', %s, 'Cliente de prueba E2E')
            """,
            (customer_document,),
        )
        customer_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO vehicles (plate, vehicle_type) VALUES (%s, 'Carro')",
            (plate,),
        )
        vehicle_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO contracts (customer_id, vehicle_id)
            VALUES (%s, %s)
            """,
            (customer_id, vehicle_id),
        )
        contract_id = cursor.lastrowid

    return {
        "operatorDocument": operator_document,
        "operatorPassword": operator_password,
        "contractId": contract_id,
    }


def _unique_car_plate() -> str:
    value = uuid.uuid4().int
    letters = "".join(chr(ord("A") + (value >> shift) % 26) for shift in (0, 5, 10))
    digits = f"{(value >> 15) % 1000:03d}"
    return letters + digits


if __name__ == "__main__":
    print(json.dumps(create_fixture()))
