"""SQLite database layer for bookmark storage."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Self

from platformdirs import user_data_dir

from wut.core.models import Bookmark

# Schema version for migrations
SCHEMA_VERSION = 1

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS bookmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL UNIQUE COLLATE NOCASE,
    definition TEXT NOT NULL,
    part_of_speech TEXT NOT NULL DEFAULT '',
    phonetic TEXT,
    synonyms TEXT DEFAULT '',
    antonyms TEXT DEFAULT '',
    example TEXT,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_bookmarks_word ON bookmarks(word COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_bookmarks_added_at ON bookmarks(added_at DESC);
"""


class DatabaseError(Exception):
    """Base exception for database errors."""


class BookmarkNotFoundError(DatabaseError):
    """Raised when a bookmark is not found."""

    def __init__(self, *, word: str) -> None:
        self.word = word
        super().__init__(f"Bookmark not found: '{word}'")


class BookmarkExistsError(DatabaseError):
    """Raised when trying to add a bookmark that already exists."""

    def __init__(self, *, word: str) -> None:
        self.word = word
        super().__init__(f"Bookmark already exists: '{word}'")


class Database:
    """SQLite database connection manager."""

    def __init__(self, *, db_path: Path | None = None) -> None:
        """Initialize database with optional custom path.

        Args:
            db_path: Path to database file. If None, uses platform default.
        """
        self._db_path = db_path or self._get_default_path()
        self._connection: sqlite3.Connection | None = None

    @staticmethod
    def _get_default_path() -> Path:
        """Get platform-appropriate database path."""
        data_dir = Path(user_data_dir(appname="wut", appauthor="wut-cli", ensure_exists=True))
        return data_dir / "bookmarks.db"

    @property
    def db_path(self) -> Path:
        """Get the database file path."""
        return self._db_path

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._connection is None:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(self._db_path)
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._initialize_schema()
        return self._connection

    def _initialize_schema(self) -> None:
        """Initialize database schema if needed."""
        conn = self._connection
        if conn is None:
            return

        # Check schema version
        cursor = conn.execute("PRAGMA user_version")
        current_version = cursor.fetchone()[0]

        if current_version < SCHEMA_VERSION:
            conn.executescript(SCHEMA_SQL)
            conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
            conn.commit()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Context manager for database connection."""
        conn = self._get_connection()
        try:
            yield conn
        except sqlite3.Error as e:
            conn.rollback()
            raise DatabaseError(f"Database error: {e}") from e

    def close(self) -> None:
        """Close database connection."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self) -> Self:
        """Enter context manager."""
        self._get_connection()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit context manager."""
        self.close()


class BookmarkRepository:
    """Repository for bookmark CRUD operations."""

    def __init__(self, *, database: Database) -> None:
        """Initialize repository with database.

        Args:
            database: Database instance to use.
        """
        self._db = database

    def add(self, *, bookmark: Bookmark) -> Bookmark:
        """Add a new bookmark.

        Args:
            bookmark: Bookmark to add.

        Returns:
            The added bookmark with ID populated.

        Raises:
            BookmarkExistsError: If bookmark for word already exists.
        """
        with self._db.connection() as conn:
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO bookmarks (
                        word, definition, part_of_speech, phonetic,
                        synonyms, antonyms, example, added_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        bookmark.word,
                        bookmark.definition,
                        bookmark.part_of_speech,
                        bookmark.phonetic,
                        bookmark.synonyms,
                        bookmark.antonyms,
                        bookmark.example,
                        bookmark.added_at.isoformat(),
                        bookmark.updated_at.isoformat(),
                    ),
                )
                conn.commit()
                bookmark.id = cursor.lastrowid
                return bookmark
            except sqlite3.IntegrityError as e:
                raise BookmarkExistsError(word=bookmark.word) from e

    def get(self, *, word: str) -> Bookmark:
        """Get a bookmark by word.

        Args:
            word: Word to look up.

        Returns:
            The bookmark.

        Raises:
            BookmarkNotFoundError: If bookmark not found.
        """
        with self._db.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM bookmarks WHERE word = ? COLLATE NOCASE",
                (word,),
            )
            row = cursor.fetchone()
            if row is None:
                raise BookmarkNotFoundError(word=word)
            return self._row_to_bookmark(row=row)

    def get_by_id(self, *, bookmark_id: int) -> Bookmark:
        """Get a bookmark by ID.

        Args:
            bookmark_id: Bookmark ID.

        Returns:
            The bookmark.

        Raises:
            BookmarkNotFoundError: If bookmark not found.
        """
        with self._db.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM bookmarks WHERE id = ?",
                (bookmark_id,),
            )
            row = cursor.fetchone()
            if row is None:
                raise BookmarkNotFoundError(word=f"ID: {bookmark_id}")
            return self._row_to_bookmark(row=row)

    def exists(self, *, word: str) -> bool:
        """Check if a bookmark exists.

        Args:
            word: Word to check.

        Returns:
            True if bookmark exists.
        """
        with self._db.connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM bookmarks WHERE word = ? COLLATE NOCASE",
                (word,),
            )
            return cursor.fetchone() is not None

    def list_all(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Bookmark]:
        """List all bookmarks with pagination.

        Args:
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            List of bookmarks.
        """
        with self._db.connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM bookmarks
                ORDER BY added_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
            return [self._row_to_bookmark(row=row) for row in cursor.fetchall()]

    def search(self, *, query: str, limit: int = 20) -> list[Bookmark]:
        """Search bookmarks by word.

        Args:
            query: Search query (prefix match).
            limit: Maximum number of results.

        Returns:
            List of matching bookmarks.
        """
        with self._db.connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM bookmarks
                WHERE word LIKE ? COLLATE NOCASE
                ORDER BY word
                LIMIT ?
                """,
                (f"{query}%", limit),
            )
            return [self._row_to_bookmark(row=row) for row in cursor.fetchall()]

    def delete(self, *, word: str) -> bool:
        """Delete a bookmark by word.

        Args:
            word: Word to delete.

        Returns:
            True if deleted, False if not found.
        """
        with self._db.connection() as conn:
            cursor = conn.execute(
                "DELETE FROM bookmarks WHERE word = ? COLLATE NOCASE",
                (word,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def count(self) -> int:
        """Get total number of bookmarks.

        Returns:
            Number of bookmarks.
        """
        with self._db.connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM bookmarks")
            result = cursor.fetchone()
            return int(result[0]) if result else 0

    def clear(self) -> int:
        """Delete all bookmarks.

        Returns:
            Number of deleted bookmarks.
        """
        with self._db.connection() as conn:
            cursor = conn.execute("DELETE FROM bookmarks")
            conn.commit()
            return cursor.rowcount

    @staticmethod
    def _row_to_bookmark(*, row: sqlite3.Row) -> Bookmark:
        """Convert database row to Bookmark model."""
        return Bookmark(
            id=row["id"],
            word=row["word"],
            definition=row["definition"],
            part_of_speech=row["part_of_speech"],
            phonetic=row["phonetic"],
            synonyms=row["synonyms"],
            antonyms=row["antonyms"],
            example=row["example"],
            added_at=datetime.fromisoformat(row["added_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
