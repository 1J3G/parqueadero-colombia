from decimal import Decimal

from app.database import transaction
from payment_integration_support import PaymentIntegrationTestCase


class PaymentRegistrationIntegrationTest(PaymentIntegrationTestCase):
    def test_cash_payment_activates_contract_and_persists_receipt(self):
        response = self.client.post("/api/payments", json=self.payment_payload())

        self.assertEqual(response.status_code, 201, response.text)
        result = response.json()
        receipt_response = self.client.get(f"/api/receipts/{result['payment_id']}")

        self.assertEqual(receipt_response.status_code, 200, receipt_response.text)
        receipt = receipt_response.json()
        self.assertEqual(receipt["consecutive_number"], result["receipt_number"])
        self.assertEqual(receipt["customer_document"], self.customer_document)
        self.assertEqual(Decimal(str(receipt["net_amount"])), Decimal("100000.00"))
        self.assertEqual(Decimal(str(receipt["tax_amount"])), Decimal("19000.00"))
        self.assertEqual(Decimal(str(receipt["total_amount"])), Decimal("119000.00"))

        with transaction() as cursor:
            cursor.execute(
                """
                SELECT p.operator_id, p.cash_opening_id, p.status, c.status AS contract_status,
                       c.starts_on, c.expires_on
                FROM payments p
                JOIN contracts c ON c.id = p.contract_id
                WHERE p.id = %s
                """,
                (result["payment_id"],),
            )
            persisted = cursor.fetchone()

        self.assertEqual(persisted["operator_id"], self.operator_id)
        self.assertEqual(persisted["cash_opening_id"], self.cash_id)
        self.assertEqual(persisted["status"], "Registrado")
        self.assertEqual(persisted["contract_status"], "Activo")
        self.assertEqual(str(persisted["starts_on"]), result["starts_on"])
        self.assertEqual(str(persisted["expires_on"]), result["expires_on"])
