"""Database service: MySQL connection and metadata queries."""

import os
from typing import List

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error as MySQLError
from mysql.connector.connection import MySQLConnection

from models.table_metadata import ColumnInfo, TableMetadata

# Load .env variables once at module import time
load_dotenv()


class DBConnectionError(Exception):
    """Raised when the database connection cannot be established."""


class DBQueryError(Exception):
    """Raised when a database query fails."""


def _get_connection() -> MySQLConnection:
    """Create and return a MySQL connection using environment variables.

    Raises:
        DBConnectionError: If the connection cannot be established.
    """
    host = os.getenv("DB_HOST", "localhost")
    port_str = os.getenv("DB_PORT", "3306")
    try:
        port = int(port_str)
    except ValueError:
        raise DBConnectionError(
            f"DB_PORT must be a valid integer, got '{port_str}'."
        )
    user = os.getenv("DB_USER", "")
    password = os.getenv("DB_PASSWORD", "")
    database = os.getenv("DB_NAME", "")

    if not user or not database:
        raise DBConnectionError(
            "DB_USER and DB_NAME must be set in the .env file."
        )

    try:
        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            connection_timeout=10,
        )
        return connection  # type: ignore[return-value]
    except MySQLError as exc:
        raise DBConnectionError(
            f"Could not connect to MySQL: {exc}"
        ) from exc


def get_tables() -> List[str]:
    """Return a sorted list of table names from the configured database.

    Raises:
        DBConnectionError: On connection failure.
        DBQueryError: On query failure.
    """
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        rows = cursor.fetchall()
        return sorted(row[0] for row in rows)
    except MySQLError as exc:
        raise DBQueryError(f"Failed to retrieve tables: {exc}") from exc
    finally:
        conn.close()


def get_table_metadata(table_name: str) -> TableMetadata:
    """Return column metadata for the given table.

    Args:
        table_name: Name of the MySQL table to inspect.

    Raises:
        DBConnectionError: On connection failure.
        DBQueryError: On query failure.
    """
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        # Use parameterised query via INFORMATION_SCHEMA to avoid SQL injection
        cursor.execute(
            """
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
            """,
            (table_name,),
        )
        rows = cursor.fetchall()
        columns = [
            ColumnInfo(
                name=row[0],
                data_type=row[1],
                is_nullable=(row[2].upper() == "YES"),
            )
            for row in rows
        ]
        return TableMetadata(table_name=table_name, columns=columns)
    except MySQLError as exc:
        raise DBQueryError(
            f"Failed to retrieve metadata for '{table_name}': {exc}"
        ) from exc
    finally:
        conn.close()
