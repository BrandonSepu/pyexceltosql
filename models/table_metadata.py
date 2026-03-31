"""Table metadata model: holds column names and types for a MySQL table."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ColumnInfo:
    """Information about a single database column."""

    name: str
    data_type: str
    is_nullable: bool


@dataclass
class TableMetadata:
    """Metadata for a MySQL table, including its columns."""

    table_name: str
    columns: List[ColumnInfo] = field(default_factory=list)

    @property
    def column_names(self) -> List[str]:
        """Return a list of column names."""
        return [col.name for col in self.columns]
