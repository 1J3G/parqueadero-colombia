import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import Mock

from app.payments import register_payment


class PaymentRenewalTest(unittest.TestCase):
    def register_payment_with_expiration(self, contract, latest_expiration, payment_date):
        cursor = Mock()
        cursor.fetchone.side_effect = [
            contract,
            {"id": contract["vehicle_id"]},
            {"payment_date": payment_date},
            {"latest_expiration": latest_expiration},
            {
                "document_type": contract["document_type"],
                "document": contract["document"],
                "full_name": contract["full_name"],
            },
            {"last_number": 40},
        ]
        cursor.lastrowid = 90

        result = register_payment(
            cursor,
            contract["id"],
            {"id": 3, "user_id": 2},
            1,
            Decimal("100.00"),
            "Efectivo",
            None,
        )
        return cursor, result

    def test_new_contract_starts_after_latest_active_contract_for_same_customer_and_vehicle(self):
        contract = {
            "id": 12,
            "status": "Pendiente de Pago",
            "starts_on": None,
            "expires_on": None,
            "customer_id": 7,
            "vehicle_id": 4,
            "document_type": "CC",
            "document": "123",
            "full_name": "Cliente de prueba",
        }
        cursor, result = self.register_payment_with_expiration(
            contract, date(2026, 11, 30), date(2026, 11, 11)
        )

        self.assertEqual(result["starts_on"], date(2026, 12, 1))
        self.assertEqual(result["expires_on"], date(2026, 12, 30))
        contract_update = next(
            call for call in cursor.execute.call_args_list if "UPDATE contracts SET status" in call.args[0]
        )
        self.assertEqual(
            contract_update.args[1],
            (date(2026, 12, 1), date(2026, 12, 30), 12),
        )
        expiration_query = next(
            call for call in cursor.execute.call_args_list if "MAX(expires_on)" in call.args[0]
        )
        vehicle_lock_index = next(
            index
            for index, call in enumerate(cursor.execute.call_args_list)
            if "FROM vehicles" in call.args[0] and "FOR UPDATE" in call.args[0]
        )
        expiration_query_index = cursor.execute.call_args_list.index(expiration_query)
        self.assertLess(vehicle_lock_index, expiration_query_index)
        self.assertIn("customer_id = %s", expiration_query.args[0])
        self.assertIn("vehicle_id = %s", expiration_query.args[0])
        self.assertIn("status = 'Activo'", expiration_query.args[0])
        self.assertEqual(
            expiration_query.args[1],
            (7, 4, date(2026, 11, 11)),
        )

    def test_new_contract_without_an_active_period_starts_on_payment_date(self):
        contract = {
            "id": 12,
            "status": "Pendiente de Pago",
            "starts_on": None,
            "expires_on": None,
            "customer_id": 7,
            "vehicle_id": 4,
            "document_type": "CC",
            "document": "123",
            "full_name": "Cliente de prueba",
        }

        _, result = self.register_payment_with_expiration(
            contract, None, date(2026, 11, 11)
        )

        self.assertEqual(result["starts_on"], date(2026, 11, 11))
        self.assertEqual(result["expires_on"], date(2026, 12, 11))

    def test_renewal_keeps_start_date_of_current_contract(self):
        contract = {
            "id": 12,
            "status": "Activo",
            "starts_on": date(2026, 10, 30),
            "expires_on": date(2026, 11, 30),
            "customer_id": 7,
            "vehicle_id": 4,
            "document_type": "CC",
            "document": "123",
            "full_name": "Cliente de prueba",
        }

        _, result = self.register_payment_with_expiration(
            contract, date(2026, 11, 30), date(2026, 11, 11)
        )

        self.assertEqual(result["starts_on"], date(2026, 10, 30))
        self.assertEqual(result["expires_on"], date(2026, 12, 30))


if __name__ == "__main__":
    unittest.main()
