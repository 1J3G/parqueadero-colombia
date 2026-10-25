import hashlib
import hmac
import os
import secrets
from typing import Any

from fastapi import Depends, HTTPException, Request

from app.database import transaction

HASH_ROUNDS = 600_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, HASH_ROUNDS)
    return f"pbkdf2_sha256${HASH_ROUNDS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, rounds, salt_hex, digest_hex = stored_hash.split("$", maxsplit=3)
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(rounds),
        )
        return hmac.compare_digest(candidate.hex(), digest_hex)
    except (TypeError, ValueError):
        return False


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(cursor: Any, user_id: int) -> str:
    token = secrets.token_urlsafe(48)
    cursor.execute(
        "INSERT INTO user_sessions (user_id, token_hash) VALUES (%s, %s)",
        (user_id, token_digest(token)),
    )
    return token


def get_current_user(request: Request) -> dict[str, Any]:
    token = request.cookies.get("parking_session")
    if not token:
        raise HTTPException(status_code=401, detail="Inicie sesión para continuar.")
    with transaction() as cursor:
        cursor.execute(
            """
            SELECT u.id, u.document, u.role
            FROM user_sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = %s AND s.revoked_at IS NULL
            """,
            (token_digest(token),),
        )
        user = cursor.fetchone()
    if user is None:
        raise HTTPException(status_code=401, detail="La sesión no está activa.")
    return user


def require_administrator(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    if user["role"] != "Administrador":
        raise HTTPException(status_code=403, detail="Esta operación requiere rol Administrador.")
    return user


def cookie_is_secure() -> bool:
    return os.getenv("COOKIE_SECURE", "false").lower() == "true"
