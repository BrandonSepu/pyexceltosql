"""Unit tests for utils/validators.py."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from utils.validators import validate_columns


class TestValidateColumns:
    def test_exact_match(self):
        compat, missing, extra = validate_columns(["a", "b"], ["a", "b"])
        assert compat is True
        assert missing == []
        assert extra == []

    def test_excel_is_subset_of_db(self):
        """Excel has fewer columns than DB – still compatible."""
        compat, missing, extra = validate_columns(["a"], ["a", "b", "c"])
        assert compat is True
        assert missing == ["b", "c"]
        assert extra == []

    def test_excel_has_extra_column(self):
        """Excel has a column that does not exist in DB – not compatible."""
        compat, missing, extra = validate_columns(["a", "x"], ["a", "b"])
        assert compat is False
        assert extra == ["x"]
        assert missing == ["b"]

    def test_completely_different(self):
        compat, missing, extra = validate_columns(["x", "y"], ["a", "b"])
        assert compat is False
        assert sorted(extra) == ["x", "y"]
        assert sorted(missing) == ["a", "b"]

    def test_empty_excel_columns(self):
        compat, missing, extra = validate_columns([], ["a", "b"])
        assert compat is True
        assert missing == ["a", "b"]
        assert extra == []

    def test_both_empty(self):
        compat, missing, extra = validate_columns([], [])
        assert compat is True
        assert missing == []
        assert extra == []
