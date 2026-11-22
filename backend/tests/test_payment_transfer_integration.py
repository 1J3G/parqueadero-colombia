from app.database import transaction
from payment_integration_support import PaymentIntegrationTestCase


class PaymentTransferIntegrationTest(PaymentIntegrationTestCase):
    def test_transfer_requires_reference_and_saves_valid_reference(self):
        missing_reference = self.client.post(
            "/api/payments",
            json=self.payment_payload(
                payment_method="Transferencia Bancaria",
                reference_code=" ",
            ),
        )

        self.assertEqual(missing_reference.status_code, 400, missing_reference.text)
        with transaction() as cursor:
            cursor.execute("SELECT COUNT(*) AS count FROM payments WHERE contract_id = %s", (self.contract_id,))
            self.assertEqual(cursor.fetchone()["count"], 0)

        reference = f"TEST-{self.customer_document}"
        payment = self.client.post(
            "/api/payments",
            json=self.payment_payload(
                payment_method="Transferencia Bancaria",
                reference_code=reference,
            ),
        )

        self.assertEqual(payment.status_code, 201, payment.text)
        with transaction() as cursor:
            cursor.execute(
                "SELECT payment_method, reference_code FROM payments WHERE id = %s",
                (payment.json()["payment_id"],),
            )
            persisted = cursor.fetchone()

        self.assertEqual(persisted["payment_method"], "Transferencia Bancaria")
        self.assertEqual(persisted["reference_code"], reference)
