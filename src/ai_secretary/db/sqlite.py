"""SQLite access layer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3


@dataclass
class SQLiteClient:
    """Simple SQLite client wrapper."""

    db_path: Path

    def connect(self) -> sqlite3.Connection:
        """Create a SQLite connection."""
        return sqlite3.connect(self.db_path)
