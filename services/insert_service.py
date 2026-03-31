"""Insert service: batch-inserts DataFrame rows into a MySQL table."""

import math
from typing import Callable, List, Optional, Tuple

import pandas as pd
from mysql.connector import Error as MySQLError

from services.db_service import DBConnectionError, _get_connection

# Number of rows per INSERT batch
BATCH_SIZE = 500


class InsertError(Exception):
    """Raised when the insertion process encounters a fatal error."""


def insert_dataframe(
    df: pd.DataFrame,
    table_name: str,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Tuple[int, List[str]]:
    """Insert all rows of *df* into *table_name* using batched transactions.

    Args:
        df: DataFrame whose columns match the target table.
        table_name: Name of the destination MySQL table.
        progress_callback: Optional callable invoked after each batch with
            (rows_inserted_so_far, total_rows).

    Returns:
        A tuple of (successful_count, error_messages).

    Raises:
        DBConnectionError: If the connection cannot be established.
        InsertError: If the table name is invalid.
    """
    if not table_name or not table_name.replace("_", "").isalnum():
        raise InsertError(f"Invalid table name: '{table_name}'")

    columns: List[str] = list(df.columns)
    # Build parameterised INSERT statement
    col_list = ", ".join(f"`{col}`" for col in columns)
    placeholders = ", ".join(["%s"] * len(columns))
    sql = f"INSERT INTO `{table_name}` ({col_list}) VALUES ({placeholders})"

    total_rows = len(df)
    inserted = 0
    errors: List[str] = []

    conn = _get_connection()
    try:
        cursor = conn.cursor()
        conn.autocommit = False

        num_batches = math.ceil(total_rows / BATCH_SIZE)
        for batch_idx in range(num_batches):
            start = batch_idx * BATCH_SIZE
            end = min(start + BATCH_SIZE, total_rows)
            batch_df = df.iloc[start:end]

            # Convert NaN → None so MySQL receives NULL
            rows = [
                tuple(None if (isinstance(v, float) and math.isnan(v)) else v
                      for v in row)
                for row in batch_df.itertuples(index=False, name=None)
            ]

            try:
                cursor.executemany(sql, rows)
                conn.commit()
                inserted += len(rows)
            except MySQLError as exc:
                conn.rollback()
                errors.append(
                    f"Batch {batch_idx + 1}/{num_batches} failed "
                    f"(rows {start + 1}-{end}): {exc}"
                )

            if progress_callback is not None:
                progress_callback(inserted, total_rows)
    finally:
        conn.close()

    return inserted, errors
