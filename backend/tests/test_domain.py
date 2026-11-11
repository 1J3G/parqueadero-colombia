import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import Mock

from fastapi import HTTPException

from app.auth import hash_password, verify_password
from app.contracts import cancel_contract, mark_expired_contracts
from app.domain import calculate_tax, compatible_cell, require_entry_permission, renewed_expiration, validate_plate


class DomainRulesTest(unittest.TestCase):
    def test_plate_formats_follow_vehicle_type(self):
        self.assertEqual(validate_plate("abc123", "Carro"), "ABC123")
        self.assertEqual(validate_plate("abc12d", "Moto"), "ABC12D")
        self.assertEqual(validate_plate("abc123", "Camioneta"), "ABC123")
        with self.assertRaises(HTTPException):
            validate_plate("ABC12D", "Carro")

    def test_disabled_cell_only_accepts_car(self):
        self.assertTrue(compatible_cell("Carro", "Discapacitado"))
        self.assertFalse(compatible_cell("Moto", "Discapacitado"))
        self.assertFalse(compatible_cell("Camioneta", "Discapacitado"))

    def test_entry_requires_active_unexpired_contract_or_exception_for_allowed_statuses(self):
        require_entry_permission(
            "Activo", date(2026, 10, 24), date(2026, 10, 24), date(2026, 10, 24), False
        )
        require_entry_permission("Vencido", None, None, date(2026, 10, 24), True)
        with self.assertRaises(HTTPException):
            require_entry_permission(
                "Activo", date(2026, 10, 1), date(2026, 10, 23), date(2026, 10, 24), True
            )
        with self.assertRaises(HTTPException):
            require_entry_permission(
                "Activo", date(2026, 10, 25), date(2026, 11, 24), date(2026, 10, 24), False
            )
        with self.assertRaises(HTTPException):
            require_entry_permission("Pendiente de Pago", None, None, date(2026, 10, 24), False)

    def test_renewal_uses_current_expiration_or_payment_day(self):
        self.assertEqual(
            renewed_expiration("Activo", date(2026, 11, 30), 1, date(2026, 10, 24)),
            date(2026, 12, 30),
        )
        self.assertEqual(
            renewed_expiration("Pendiente de Pago", date(2026, 11, 30), 1, date(2026, 11, 11)),
            date(2026, 12, 30),
        )
        self.assertEqual(
            renewed_expiration("Vencido", date(2026, 9, 30), 1, date(2026, 10, 24)),
            date(2026, 11, 24),
        )

    def test_cancelled_contract_cannot_be_reactivated(self):
        with self.assertRaises(HTTPException):
            renewed_expiration("Cancelado", None, 1, date(2026, 10, 24))

    def test_expired_active_contracts_are_persisted_as_expired(self):
        cursor = Mock()

        mark_expired_contracts(cursor)

        query = cursor.execute.call_args.args[0]
        self.assertIn("SET status = 'Vencido'", query)
        self.assertIn("status = 'Activo'", query)
        self.assertIn("expires_on < CURRENT_DATE()", query)

    def test_contract_cancellation_requires_and_stores_administrator_justification(self):
        cursor = Mock()
        cursor.fetchone.return_value = {"id": 7, "status": "Activo"}
        cursor.rowcount = 1

        result = cancel_contract(cursor, 7, 3, "Solicitud del cliente")

        self.assertEqual(result["status"], "Cancelado")
        update_call = cursor.execute.call_args_list[1]
        self.assertIn("cancellation_justification", update_call.args[0])
        self.assertEqual(update_call.args[1], (3, "Solicitud del cliente", 7))

    def test_cancelled_contract_cannot_be_cancelled_twice(self):
        cursor = Mock()
        cursor.fetchone.return_value = {"id": 7, "status": "Cancelado"}

        with self.assertRaises(HTTPException) as raised:
            cancel_contract(cursor, 7, 3, "Justificación")

        self.assertEqual(raised.exception.status_code, 409)
        cursor.execute.assert_called_once()

    def test_tax_is_rounded_to_currency_precision(self):
        self.assertEqual(calculate_tax(Decimal("100.00")), Decimal("19.00"))
        self.assertEqual(calculate_tax(Decimal("0.05")), Decimal("0.01"))

    def test_password_hash_verifies_only_the_original_password(self):
        stored_hash = hash_password("Clave de prueba")
        self.assertTrue(verify_password("Clave de prueba", stored_hash))
        self.assertFalse(verify_password("otra clave", stored_hash))


if __name__ == "__main__":
    unittest.main()
