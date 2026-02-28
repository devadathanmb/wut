"""Bookmark manager for high-level bookmark operations."""

from pathlib import Path

from wut.core.database import (
    BookmarkExistsError,
    BookmarkNotFoundError,
    BookmarkRepository,
    Database,
)
from wut.core.models import Bookmark, Word


class BookmarkManager:
    """High-level manager for bookmark operations."""

    def __init__(self, *, db_path: Path | None = None) -> None:
        """Initialize bookmark manager.

        Args:
            db_path: Optional custom database path.
        """
        self._db = Database(db_path=db_path)
        self._repo = BookmarkRepository(database=self._db)

    @property
    def db_path(self) -> Path:
        """Get the database file path."""
        return self._db.db_path

    def add_word(self, *, word: Word) -> Bookmark:
        """Add a word to bookmarks.

        Args:
            word: Word object to bookmark.

        Returns:
            The created bookmark.

        Raises:
            BookmarkExistsError: If word is already bookmarked.
        """
        bookmark = Bookmark.from_word(word=word)
        return self._repo.add(bookmark=bookmark)

    def add_bookmark(self, *, bookmark: Bookmark) -> Bookmark:
        """Add a bookmark directly.

        Args:
            bookmark: Bookmark to add.

        Returns:
            The created bookmark.

        Raises:
            BookmarkExistsError: If bookmark already exists.
        """
        return self._repo.add(bookmark=bookmark)

    def get(self, *, word: str) -> Bookmark:
        """Get a bookmark by word.

        Args:
            word: Word to look up.

        Returns:
            The bookmark.

        Raises:
            BookmarkNotFoundError: If bookmark not found.
        """
        return self._repo.get(word=word)

    def exists(self, *, word: str) -> bool:
        """Check if a word is bookmarked.

        Args:
            word: Word to check.

        Returns:
            True if bookmarked.
        """
        return self._repo.exists(word=word)

    def list_all(self, *, limit: int = 50, offset: int = 0) -> list[Bookmark]:
        """List all bookmarks.

        Args:
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            List of bookmarks.
        """
        return self._repo.list_all(limit=limit, offset=offset)

    def search(self, query: str, *, limit: int = 20) -> list[Bookmark]:
        """Search bookmarks.

        Args:
            query: Search query.
            limit: Maximum results.

        Returns:
            Matching bookmarks.
        """
        return self._repo.search(query=query, limit=limit)

    def delete(self, *, word: str) -> bool:
        """Delete a bookmark.

        Args:
            word: Word to delete.

        Returns:
            True if deleted.
        """
        return self._repo.delete(word=word)

    def count(self) -> int:
        """Get total bookmark count.

        Returns:
            Number of bookmarks.
        """
        return self._repo.count()

    def clear(self) -> int:
        """Delete all bookmarks.

        Returns:
            Number of deleted bookmarks.
        """
        return self._repo.clear()

    def close(self) -> None:
        """Close database connection."""
        self._db.close()

    def __enter__(self) -> "BookmarkManager":
        """Enter context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit context manager."""
        self.close()


# Re-export exceptions for convenience
__all__ = [
    "BookmarkManager",
    "BookmarkExistsError",
    "BookmarkNotFoundError",
]
