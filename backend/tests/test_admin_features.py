import unittest
from datetime import date
from unittest.mock import MagicMock, Mock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.auth import get_current_user, require_administrator
from app.main import app
from app.routes.cells import CellStatusUpdate, list_cells, update_cell_status
from app.routes.contracts import list_contract_cancellations, list_contracts
from app.routes.transits import EntryRequest, register_entry
from app.routes.users import UserCreate, create_user


class AdministrativeFeaturesTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        app.dependency_overrides.clear()

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_cells_endpoint_filters_for_entry_to_free_compatible_cells(self):
        cursor = Mock()
        cursor.fetchall.return_value = [
            {"id": 1, "category": "Carro", "status": "Libre", "plate": None},
            {"id": 2, "category": "Moto", "status": "Libre", "plate": None},
            {"id": 3, "category": "Carro", "status": "En mantenimiento", "plate": None},
            {"id": 4, "category": "Carro", "status": "Ocupado", "plate": "ABC123"},
        ]
        transaction = MagicMock()
        transaction.__enter__ = Mock(return_value=cursor)
        transaction.__exit__ = Mock(return_value=False)

        with patch("app.routes.cells.transaction", return_value=transaction):
            result = list_cells(vehicle_type="Carro", _user={"id": 1})

        self.assertEqual([cell["id"] for cell in result], [1])

    def test_occupied_cell_cannot_be_changed_manually(self):
        cursor = Mock()
        cursor.fetchone.return_value = {"status": "Ocupado"}
        transaction = MagicMock()
        transaction.__enter__ = Mock(return_value=cursor)
        transaction.__exit__ = Mock(return_value=False)

        with patch("app.routes.cells.transaction", return_value=transaction):
            with self.assertRaises(HTTPException) as raised:
                update_cell_status(4, CellStatusUpdate(status="En mantenimiento"), _administrator={"id": 1})

        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(cursor.execute.call_count, 1)

    def test_free_cell_can_be_put_in_maintenance(self):
        cursor = Mock()
        cursor.fetchone.return_value = {"status": "Libre"}
        transaction = MagicMock()
        transaction.__enter__.return_value = cursor
        transaction.__exit__.return_value = False

        with patch("app.routes.cells.transaction", return_value=transaction):
            result = update_cell_status(
                3,
                CellStatusUpdate(status="En mantenimiento"),
                _administrator={"id": 1},
            )

        self.assertEqual(result["status"], "En mantenimiento")
        self.assertEqual(cursor.execute.call_args.args[1], ("En mantenimiento", 3, "Libre"))

    def test_user_creation_stores_hash_and_never_returns_credentials(self):
        cursor = Mock()
        cursor.lastrowid = 12
        transaction = MagicMock()
        transaction.__enter__ = Mock(return_value=cursor)
        transaction.__exit__ = Mock(return_value=False)

        with (
            patch("app.routes.users.transaction", return_value=transaction),
            patch("app.routes.users.hash_password", return_value="stored-hash"),
        ):
            result = create_user(
                UserCreate(document="  12345 ", password="secret", role="Operario"),
                _administrator={"id": 1},
            )

        self.assertEqual(result, {"id": 12, "document": "12345", "role": "Operario"})
        self.assertNotIn("password", result)
        self.assertNotIn("password_hash", result)
        self.assertEqual(cursor.execute.call_args.args[1], ("12345", "stored-hash", "Operario"))

    def test_users_api_rejects_operator(self):
        app.dependency_overrides[get_current_user] = lambda: {"id": 2, "role": "Operario"}

        response = self.client.post(
            "/api/users",
            json={"document": "123", "password": "secret", "role": "Administrador"},
        )

        self.assertEqual(response.status_code, 403)

    def test_cell_maintenance_api_rejects_operator(self):
        app.dependency_overrides[get_current_user] = lambda: {"id": 2, "role": "Operario"}

        response = self.client.patch(
            "/api/cells/3/status",
            json={"status": "En mantenimiento"},
        )

        self.assertEqual(response.status_code, 403)

    def test_contract_cancellation_audit_rejects_operator(self):
        app.dependency_overrides[get_current_user] = lambda: {"id": 2, "role": "Operario"}

        response = self.client.get("/api/contracts/cancellations")

        self.assertEqual(response.status_code, 403)

    def test_contract_cancellation_audit_includes_auditor_and_justification(self):
        cursor = Mock()
        cursor.fetchall.return_value = [
            {
                "contract_id": 8,
                "administrator_document": "900",
                "cancellation_justification": "Solicitud del cliente",
            }
        ]
        transaction = MagicMock()
        transaction.__enter__ = Mock(return_value=cursor)
        transaction.__exit__ = Mock(return_value=False)

        with patch("app.routes.contracts.transaction", return_value=transaction):
            result = list_contract_cancellations(_administrator={"id": 1})

        self.assertEqual(result[0]["administrator_document"], "900")
        self.assertEqual(result[0]["cancellation_justification"], "Solicitud del cliente")
        self.assertIn("c.cancelled_at", cursor.execute.call_args.args[0])

    def test_contract_listing_reports_vehicle_inside_and_occupied_cell(self):
        cursor = Mock()
        cursor.fetchall.return_value = [
            {"id": 5, "vehicle_inside": 1, "occupied_cell_label": "AUT01"}
        ]
        transaction = MagicMock()
        transaction.__enter__.return_value = cursor
        transaction.__exit__.return_value = False

        with patch("app.routes.contracts.transaction", return_value=transaction):
            result = list_contracts(_user={"id": 1})

        self.assertIs(result[0]["vehicle_inside"], True)
        self.assertEqual(result[0]["occupied_cell_label"], "AUT01")
        query = cursor.execute.call_args.args[0]
        self.assertIn("WHERE t.vehicle_id = v.id", query)
        self.assertIn("ORDER BY t.occurred_at DESC, t.id DESC", query)

    def test_entry_rejects_vehicle_already_inside_before_checking_another_cell(self):
        cursor = Mock()
        cursor.fetchone.side_effect = [
            {
                "contract_id": 5,
                "status": "Activo",
                "expires_on": date.today(),
                "vehicle_id": 10,
                "vehicle_type": "Carro",
            },
            {"id": 10},
            {"server_date": date.today()},
            {"direction": "Entrada", "cell_id": 3},
        ]
        transaction = MagicMock()
        transaction.__enter__.return_value = cursor
        transaction.__exit__.return_value = False

        with patch("app.routes.transits.transaction", return_value=transaction):
            with self.assertRaises(HTTPException) as raised:
                register_entry(
                    EntryRequest(contract_id=5, cell_id=4),
                    operator={"id": 2, "role": "Administrador"},
                )

        self.assertEqual(raised.exception.status_code, 409)
        executed_queries = [call.args[0] for call in cursor.execute.call_args_list]
        self.assertTrue(any("SELECT id FROM vehicles WHERE id = %s FOR UPDATE" in query for query in executed_queries))
        self.assertTrue(any("WHERE vehicle_id = %s" in query for query in executed_queries))
        self.assertFalse(any("SELECT id, category, status FROM cells" in query for query in executed_queries))
        self.assertFalse(any("INSERT INTO transits" in query for query in executed_queries))

    def test_administrator_requirement_rejects_operator(self):
        with self.assertRaises(HTTPException) as raised:
            require_administrator({"id": 4, "role": "Operario"})

        self.assertEqual(raised.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
