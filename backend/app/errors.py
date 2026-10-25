import logging

import mysql.connector
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def database_http_error(error: mysql.connector.Error) -> HTTPException:
    if isinstance(error, mysql.connector.IntegrityError):
        return HTTPException(status_code=409, detail="La operación entra en conflicto con los datos existentes.")
    logger.exception("Database operation failed", exc_info=error)
    return HTTPException(status_code=503, detail="No fue posible completar la operación en la base de datos.")
