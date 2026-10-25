from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from app.auth import cookie_is_secure, create_session, get_current_user, token_digest, verify_password
from app.database import transaction

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document: str = Field(min_length=1, max_length=30)
    password: str = Field(min_length=1, max_length=256)


@router.post("/login")
def login(payload: LoginRequest, response: Response) -> dict[str, str]:
    with transaction() as cursor:
        cursor.execute(
            "SELECT id, document, password_hash, role FROM users WHERE document = %s",
            (payload.document.strip(),),
        )
        user = cursor.fetchone()
        if user is None or not verify_password(payload.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Documento o contraseña incorrectos.")
        token = create_session(cursor, user["id"])
    response.set_cookie(
        key="parking_session",
        value=token,
        httponly=True,
        secure=cookie_is_secure(),
        samesite="lax",
        path="/",
    )
    return {"document": user["document"], "role": user["role"]}


@router.post("/logout", status_code=204)
def logout(request: Request, user: dict = Depends(get_current_user)) -> Response:
    token = request.cookies.get("parking_session")
    if token is None:
        raise HTTPException(status_code=401, detail="La sesión no está activa.")
    with transaction() as cursor:
        cursor.execute(
            "UPDATE user_sessions SET revoked_at = CURRENT_TIMESTAMP(6) WHERE token_hash = %s AND revoked_at IS NULL",
            (token_digest(token),),
        )
    response = Response(status_code=204)
    response.delete_cookie(
        key="parking_session",
        path="/",
        httponly=True,
        secure=cookie_is_secure(),
        samesite="lax",
    )
    return response


@router.get("/me")
def current_session(user: dict = Depends(get_current_user)) -> dict[str, str]:
    return {"document": user["document"], "role": user["role"]}
