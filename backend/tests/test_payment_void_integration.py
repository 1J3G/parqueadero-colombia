from app.database import transaction
from payment_integration_support import PaymentIntegrationTestCase


class PaymentVoidIntegrationTest(PaymentIntegrationTestCase):
    def test_only_administrator_can_void_payment_with_audited_justification(self):
        payment_response = self.client.post("/api/payments", json=self.payment_payload())
        self.assertEqual(payment_response.status_code, 201, payment_response.text)
        payment_id = payment_response.json()["payment_id"]
        void_payload = {
            "administrator_password": self.administrator_password,
            "justification": "Prueba automatizada de anulacion",
        }

        operator_response = self.client.post(f"/api/payments/{payment_id}/void", json=void_payload)
        self.assertEqual(operator_response.status_code, 403)

        self.client.cookies.set("parking_session", self.administrator_token)
        invalid_password = self.client.post(
            f"/api/payments/{payment_id}/void",
            json={**void_payload, "administrator_password": "incorrecta"},
        )
        self.assertEqual(invalid_password.status_code, 403)

        successful_void = self.client.post(f"/api/payments/{payment_id}/void", json=void_payload)
        self.assertEqual(successful_void.status_code, 200, successful_void.text)
        self.assertEqual(successful_void.json()["status"], "Anulado")

        repeated_void = self.client.post(f"/api/payments/{payment_id}/void", json=void_payload)
        self.assertEqual(repeated_void.status_code, 409)

        with transaction() as cursor:
            cursor.execute("SELECT status FROM payments WHERE id = %s", (payment_id,))
            self.assertEqual(cursor.fetchone()["status"], "Anulado")
            cursor.execute(
                """
                SELECT administrator_id, justification
                FROM payment_audit
                WHERE payment_id = %s
                """,
                (payment_id,),
            )
            audit = cursor.fetchone()

        self.assertEqual(audit["administrator_id"], self.administrator_id)
        self.assertEqual(audit["justification"], void_payload["justification"])
