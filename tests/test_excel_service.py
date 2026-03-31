"""Unit tests for services/excel_service.py."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import pytest
from services.excel_service import ExcelLoadError, load_excel


def _make_xlsx(data: dict) -> str:
    """Write a DataFrame to a temporary .xlsx file and return its path."""
    tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    tmp.close()
    pd.DataFrame(data).to_excel(tmp.name, index=False)
    return tmp.name


class TestLoadExcel:
    def test_basic_load(self):
        path = _make_xlsx({"col_a": [1, 2, 3], "col_b": ["x", "y", "z"]})
        try:
            df, columns, row_count = load_excel(path)
            assert columns == ["col_a", "col_b"]
            assert row_count == 3
        finally:
            os.unlink(path)

    def test_column_names_stripped(self):
        path = _make_xlsx({"  name  ": [1], "age": [2]})
        try:
            _, columns, _ = load_excel(path)
            assert "name" in columns
        finally:
            os.unlink(path)

    def test_wrong_extension_raises(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            f.write(b"a,b\n1,2")
            name = f.name
        try:
            with pytest.raises(ExcelLoadError, match="xlsx"):
                load_excel(name)
        finally:
            os.unlink(name)

    def test_nonexistent_file_raises(self):
        path = os.path.join(tempfile.gettempdir(), "__nonexistent_file__.xlsx")
        with pytest.raises(ExcelLoadError, match="not found"):
            load_excel(path)

    def test_empty_path_raises(self):
        with pytest.raises(ExcelLoadError, match="No file path"):
            load_excel("")

    def test_empty_xlsx_raises(self):
        """A truly empty DataFrame (no columns) should raise ExcelLoadError."""
        tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        tmp.close()
        # Write an xlsx with no columns
        pd.DataFrame().to_excel(tmp.name, index=False)
        try:
            with pytest.raises(ExcelLoadError):
                load_excel(tmp.name)
        finally:
            os.unlink(tmp.name)
