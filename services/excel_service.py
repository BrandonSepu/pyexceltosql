"""Excel service: reads and validates .xlsx files using pandas/openpyxl."""

import os
from typing import List, Tuple

import pandas as pd


class ExcelLoadError(Exception):
    """Raised when the Excel file cannot be loaded or is invalid."""


def load_excel(file_path: str) -> Tuple[pd.DataFrame, List[str], int]:
    """Load an Excel file and return its data.

    Args:
        file_path: Absolute path to the .xlsx file.

    Returns:
        A tuple of (dataframe, column_names, row_count).

    Raises:
        ExcelLoadError: If the file is invalid, not .xlsx, or empty.
    """
    if not file_path:
        raise ExcelLoadError("No file path provided.")

    if not os.path.isfile(file_path):
        raise ExcelLoadError(f"File not found: {file_path}")

    _, ext = os.path.splitext(file_path)
    if ext.lower() != ".xlsx":
        raise ExcelLoadError(
            f"Invalid file type '{ext}'. Only .xlsx files are supported."
        )

    try:
        df: pd.DataFrame = pd.read_excel(file_path, engine="openpyxl")
    except Exception as exc:
        raise ExcelLoadError(f"Could not read Excel file: {exc}") from exc

    if df.empty or len(df.columns) == 0:
        raise ExcelLoadError(
            "The Excel file is empty or contains no columns."
        )

    # Normalise column names: strip surrounding whitespace
    df.columns = [str(col).strip() for col in df.columns]

    column_names: List[str] = list(df.columns)
    row_count: int = len(df)

    return df, column_names, row_count
