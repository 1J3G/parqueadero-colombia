import unittest
import uuid

from fastapi.testclient import TestClient

from app.auth import create_session, hash_password
from app.database import transaction
from app.main import app


class PaymentIntegrationTestCase(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        app.dependency_overrides.clear()
        self.operator_id = None
        self.administrator_id = None
        self.customer_id = None
        self.vehicle_id = None
        self.contract_id = None
        self.operator_token = None
        self.administrator_token = None

        with transaction() as cursor:
            cursor.execute("SELECT DATABASE() AS database_name")
            database_name = cursor.fetchone()["database_name"]
            if not database_name.endswith("_test"):
                raise RuntimeError(
                    "Payment integration tests require a database whose name ends with '_test'."
                )

        self.addCleanup(self.cleanup_test_data)

        suffix = uuid.uuid4().hex[:12].upper()
        self.operator_document = f"TO{suffix}"
        self.administrator_document = f"TA{suffix}"
        self.operator_password = f"Operator-{suffix}!"
        self.administrator_password = f"Admin-{suffix}!"
        self.customer_document = f"TC{suffix}"
        self.plate = self._unique_car_plate()

        with transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO users (document, password_hash, role)
                VALUES (%s, %s, 'Operario')
                """,
                (self.operator_document, hash_password(self.operator_password)),
            )
            self.operator_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO users (document, password_hash, role)
                VALUES (%s, %s, 'Administrador')
                """,
                (self.administrator_document, hash_password(self.administrator_password)),
            )
            self.administrator_id = cursor.lastrowid
            self.operator_token = create_session(cursor, self.operator_id)
            self.administrator_token = create_session(cursor, self.administrator_id)

        self.client.cookies.set("parking_session", self.operator_token)
        customer_response = self.client.post(
            "/api/customers",
            json={
                "document_type": "CC",
                "document": self.customer_document,
                "full_name": "Cliente de prueba automatizada",
            },
        )
        self._expect_status(customer_response, 201)
        self.customer_id = customer_response.json()["id"]

        contract_response = self.client.post(
            "/api/contracts",
            json={
                "customer_id": self.customer_id,
                "plate": self.plate,
                "vehicle_type": "Carro",
            },
        )
        self._expect_status(contract_response, 201)
        self.contract_id = contract_response.json()["id"]
        self.vehicle_id = contract_response.json()["vehicle_id"]

        cash_response = self.client.post("/api/cash/open", json={"base_amount": "50000.00"})
        self._expect_status(cash_response, 201)
        self.cash_id = cash_response.json()["id"]

    @staticmethod
    def _expect_status(response, expected_status):
        if response.status_code != expected_status:
            raise AssertionError(
                f"Expected HTTP {expected_status}, got {response.status_code}: {response.text}"
            )

    @staticmethod
    def _unique_car_plate():
        value = uuid.uuid4().int
        letters = "".join(chr(ord("A") + (value >> shift) % 26) for shift in (0, 5, 10))
        digits = f"{(value >> 15) % 1000:03d}"
        return letters + digits

    def payment_payload(self, **overrides):
        payload = {
            "contract_id": self.contract_id,
            "paid_months": 1,
            "net_amount": "100000.00",
            "payment_method": "Efectivo",
            "reference_code": None,
        }
        payload.update(overrides)
        return payload

    def cleanup_test_data(self):
        app.dependency_overrides.clear()
        if self.operator_id is None:
            return

        with transaction() as cursor:
            cursor.execute("SELECT DATABASE() AS database_name")
            database_name = cursor.fetchone()["database_name"]
            if not database_name.endswith("_test"):
                raise RuntimeError(
                    "Refusing to clean up payment tests outside a database ending with '_test'."
                )

            if self.contract_id is not None:
                cursor.execute("SELECT id FROM payments WHERE contract_id = %s", (self.contract_id,))
                payment_ids = [row["id"] for row in cursor.fetchall()]
                if payment_ids:
                    # Payment immutability triggers require preserving linked test fixtures.
                    return
                cursor.execute("DELETE FROM contracts WHERE id = %s", (self.contract_id,))

            cursor.execute("DELETE FROM cash_openings WHERE user_id = %s", (self.operator_id,))
            if self.vehicle_id is not None:
                cursor.execute("DELETE FROM vehicles WHERE id = %s", (self.vehicle_id,))
            if self.customer_id is not None:
                cursor.execute("DELETE FROM customers WHERE id = %s", (self.customer_id,))
            cursor.execute("DELETE FROM user_sessions WHERE user_id IN (%s, %s)", (self.operator_id, self.administrator_id))
            cursor.execute("DELETE FROM users WHERE id IN (%s, %s)", (self.operator_id, self.administrator_id))
