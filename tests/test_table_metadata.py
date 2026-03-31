"""Unit tests for models/table_metadata.py."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.table_metadata import ColumnInfo, TableMetadata


class TestTableMetadata:
    def test_column_names(self):
        cols = [
            ColumnInfo("id", "int", False),
            ColumnInfo("name", "varchar", True),
        ]
        meta = TableMetadata("users", cols)
        assert meta.column_names == ["id", "name"]

    def test_empty_columns(self):
        meta = TableMetadata("empty_table")
        assert meta.column_names == []

    def test_column_info_fields(self):
        col = ColumnInfo("age", "int", True)
        assert col.name == "age"
        assert col.data_type == "int"
        assert col.is_nullable is True
