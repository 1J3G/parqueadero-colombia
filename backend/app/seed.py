import getpass
import logging
import os

from app.auth import hash_password
from app.database import transaction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def read_value(environment_name: str, prompt: str, secret: bool = False) -> str:
    value = os.getenv(environment_name)
    if value is None:
        value = getpass.getpass(prompt) if secret else input(prompt)
    normalized = value if secret else value.strip()
    if not normalized.strip():
        raise ValueError(f"{environment_name} must not be empty.")
    return normalized


def seed_default_users() -> None:
    users = (
        (
            read_value("ADMIN_DOCUMENT", "Documento del Administrador: "),
            read_value("ADMIN_PASSWORD", "Contraseña del Administrador: ", secret=True),
            "Administrador",
        ),
        (
            read_value("OPERATOR_DOCUMENT", "Documento del Operario: "),
            read_value("OPERATOR_PASSWORD", "Contraseña del Operario: ", secret=True),
            "Operario",
        ),
    )
    if users[0][0] == users[1][0]:
        raise ValueError("Administrator and operator documents must be different.")

    with transaction() as cursor:
        for document, password, role in users:
            cursor.execute("SELECT role FROM users WHERE document = %s", (document,))
            existing = cursor.fetchone()
            if existing:
                if existing["role"] != role:
                    raise ValueError(f"Document {document} already exists with a different role.")
                logger.info("Existing %s account retained.", role)
                continue
            cursor.execute(
                "INSERT INTO users (document, password_hash, role) VALUES (%s, %s, %s)",
                (document, hash_password(password), role),
            )
            logger.info("Created default %s account.", role)


if __name__ == "__main__":
    seed_default_users()
