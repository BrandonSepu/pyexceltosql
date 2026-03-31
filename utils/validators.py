"""Utility validators for column compatibility checks."""

from typing import List, Tuple


def validate_columns(
    excel_columns: List[str],
    db_columns: List[str],
) -> Tuple[bool, List[str], List[str]]:
    """Compare Excel columns against database table columns.

    Args:
        excel_columns: Column names found in the Excel file.
        db_columns: Column names present in the target database table.

    Returns:
        A tuple of (compatible, missing_in_excel, extra_in_excel) where:
        - compatible (bool): True when Excel columns are a subset of db_columns
          (every Excel column exists in the table, though the table may have
          more columns that will receive NULL / default values).
        - missing_in_excel: db columns that are absent in the Excel file.
        - extra_in_excel: Excel columns that do not exist in the db table.
    """
    excel_set = set(excel_columns)
    db_set = set(db_columns)

    extra_in_excel: List[str] = sorted(excel_set - db_set)
    missing_in_excel: List[str] = sorted(db_set - excel_set)

    # Insertion is only safe when there are no unknown Excel columns.
    compatible: bool = len(extra_in_excel) == 0

    return compatible, missing_in_excel, extra_in_excel
