import logging
import os
from contextlib import contextmanager
from typing import Iterator

import mysql.connector
from fastapi import HTTPException
from mysql.connector.cursor import MySQLCursorDict
from dotenv import load_dotenv

from app.errors import database_http_error

logger = logging.getLogger(__name__)
load_dotenv()


def get_connection() -> mysql.connector.MySQLConnection:
    required = ("PARKING_DB_HOST", "PARKING_DB_NAME", "PARKING_DB_USER")
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        logger.error("Missing database configuration: %s", ", ".join(missing))
        raise HTTPException(status_code=503, detail="La base de datos no está configurada.")
    try:
        return mysql.connector.connect(
            host=os.environ["PARKING_DB_HOST"],
            port=int(os.getenv("PARKING_DB_PORT", "3306")),
            database=os.environ["PARKING_DB_NAME"],
            user=os.environ["PARKING_DB_USER"],
            password=os.getenv("PARKING_DB_PASSWORD", ""),
            charset="utf8mb4",
            collation="utf8mb4_unicode_ci",
            autocommit=False,
        )
    except mysql.connector.Error as error:
        logger.exception("Could not connect to MySQL")
        raise HTTPException(status_code=503, detail="No fue posible conectar con la base de datos.") from error


@contextmanager
def transaction() -> Iterator[MySQLCursorDict]:
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        connection.start_transaction()
        yield cursor
        connection.commit()
    except mysql.connector.Error as error:
        connection.rollback()
        raise database_http_error(error) from error
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()
