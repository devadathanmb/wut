"""Tests for database and bookmark operations."""

import sqlite3
import tempfile
from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from wut.core.bookmarks import BookmarkManager
from wut.core.database import (
    BookmarkExistsError,
    BookmarkNotFoundError,
    BookmarkRepository,
    Database,
    DatabaseError,
)
from wut.core.models import Bookmark, Word


@pytest.fixture
def temp_db_path() -> Path:
    """Create a temporary database path."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        return Path(f.name)


@pytest.fixture
def database(temp_db_path: Path) -> Generator[Database, None, None]:
    """Create a test database."""
    db = Database(db_path=temp_db_path)
    yield db
    db.close()
    temp_db_path.unlink(missing_ok=True)


@pytest.fixture
def repository(database: Database) -> BookmarkRepository:
    """Create a test repository."""
    return BookmarkRepository(database=database)


@pytest.fixture
def sample_bookmark() -> Bookmark:
    """Create a sample bookmark for testing."""
    return Bookmark(
        id=None,
        word="hello",
        definition="A greeting",
        part_of_speech="noun",
        phonetic="/həˈloʊ/",
        synonyms="hi,hey,greetings",
        antonyms="goodbye,bye",
        example="Hello, world!",
        added_at=datetime.now(),
        updated_at=datetime.now(),
    )


class TestDatabase:
    """Tests for Database class."""

    def test_creates_database_file(self, temp_db_path: Path) -> None:
        """Test that database file is created."""
        db = Database(db_path=temp_db_path)
        with db.connection():
            pass
        assert temp_db_path.exists()
        db.close()

    def test_context_manager(self, temp_db_path: Path) -> None:
        """Test database as context manager."""
        with Database(db_path=temp_db_path) as db, db.connection():
            pass
        # Should not raise after exiting context

    def test_schema_version(self, database: Database) -> None:
        """Test that schema version is set."""
        with database.connection() as conn:
            cursor = conn.execute("PRAGMA user_version")
            version = cursor.fetchone()[0]
            assert version >= 1

    def test_db_path_property(self, temp_db_path: Path) -> None:
        """Test database path property."""
        db = Database(db_path=temp_db_path)
        assert db.db_path == temp_db_path

    def test_default_path_generation(self) -> None:
        """Test default path uses platform data directory."""
        with patch("wut.core.database.user_data_dir", return_value="/tmp/wut-data"):
            path = Database._get_default_path()

        assert path == Path("/tmp/wut-data/bookmarks.db")

    def test_initialize_schema_no_connection_noop(self, temp_db_path: Path) -> None:
        """Schema initialization should no-op without an open connection."""
        db = Database(db_path=temp_db_path)
        db._initialize_schema()
        db.close()

    def test_connection_wraps_sqlite_error_and_rolls_back(self, temp_db_path: Path) -> None:
        """Convert sqlite errors into DatabaseError and roll back transaction."""
        db = Database(db_path=temp_db_path)
        mock_conn = MagicMock()

        with (
            patch.object(db, "_get_connection", return_value=mock_conn),
            pytest.raises(DatabaseError, match="Database error"),
            db.connection(),
        ):
            raise sqlite3.OperationalError("boom")

        mock_conn.rollback.assert_called_once()

    def test_close_without_open_connection(self, temp_db_path: Path) -> None:
        """Close should safely no-op before any connection is created."""
        db = Database(db_path=temp_db_path)
        db.close()


class TestBookmarkRepository:
    """Tests for BookmarkRepository class."""

    def test_add_bookmark(self, repository: BookmarkRepository, sample_bookmark: Bookmark) -> None:
        """Test adding a bookmark."""
        result = repository.add(bookmark=sample_bookmark)

        assert result.id is not None
        assert result.word == "hello"

    def test_add_duplicate_raises(
        self, repository: BookmarkRepository, sample_bookmark: Bookmark
    ) -> None:
        """Test that adding duplicate raises error."""
        repository.add(bookmark=sample_bookmark)

        with pytest.raises(BookmarkExistsError) as exc_info:
            repository.add(bookmark=sample_bookmark)

        assert exc_info.value.word == "hello"

    def test_get_bookmark(self, repository: BookmarkRepository, sample_bookmark: Bookmark) -> None:
        """Test retrieving a bookmark."""
        repository.add(bookmark=sample_bookmark)

        result = repository.get(word="hello")

        assert result.word == "hello"
        assert result.definition == "A greeting"
        assert result.phonetic == "/həˈloʊ/"

    def test_get_case_insensitive(
        self, repository: BookmarkRepository, sample_bookmark: Bookmark
    ) -> None:
        """Test that get is case insensitive."""
        repository.add(bookmark=sample_bookmark)

        result = repository.get(word="HELLO")
        assert result.word == "hello"

    def test_get_not_found_raises(self, repository: BookmarkRepository) -> None:
        """Test that getting non-existent bookmark raises error."""
        with pytest.raises(BookmarkNotFoundError) as exc_info:
            repository.get(word="nonexistent")

        assert exc_info.value.word == "nonexistent"

    def test_get_by_id(self, repository: BookmarkRepository, sample_bookmark: Bookmark) -> None:
        """Test retrieving a bookmark by ID."""
        added = repository.add(bookmark=sample_bookmark)
        assert added.id is not None

        result = repository.get_by_id(bookmark_id=added.id)

        assert result.id == added.id
        assert result.word == "hello"

    def test_get_by_id_not_found_raises(self, repository: BookmarkRepository) -> None:
        """Test that getting non-existent ID raises error."""
        with pytest.raises(BookmarkNotFoundError) as exc_info:
            repository.get_by_id(bookmark_id=99999)

        assert "ID: 99999" in exc_info.value.word

    def test_exists(self, repository: BookmarkRepository, sample_bookmark: Bookmark) -> None:
        """Test checking if bookmark exists."""
        assert not repository.exists(word="hello")

        repository.add(bookmark=sample_bookmark)

        assert repository.exists(word="hello")
        assert repository.exists(word="HELLO")  # Case insensitive

    def test_list_all(self, repository: BookmarkRepository, sample_bookmark: Bookmark) -> None:
        """Test listing all bookmarks."""
        # Add multiple bookmarks
        repository.add(bookmark=sample_bookmark)

        bookmark2 = Bookmark(
            id=None,
            word="world",
            definition="The earth",
            part_of_speech="noun",
            phonetic=None,
            synonyms="",
            antonyms="",
            example=None,
            added_at=datetime.now(),
            updated_at=datetime.now(),
        )
        repository.add(bookmark=bookmark2)

        results = repository.list_all()

        assert len(results) == 2

    def test_list_all_with_limit(self, repository: BookmarkRepository) -> None:
        """Test listing with limit."""
        for i in range(5):
            bookmark = Bookmark(
                id=None,
                word=f"word{i}",
                definition=f"Definition {i}",
                part_of_speech="noun",
                phonetic=None,
                synonyms="",
                antonyms="",
                example=None,
                added_at=datetime.now(),
                updated_at=datetime.now(),
            )
            repository.add(bookmark=bookmark)

        results = repository.list_all(limit=3)
        assert len(results) == 3

    def test_search(self, repository: BookmarkRepository) -> None:
        """Test searching bookmarks."""
        words = ["apple", "application", "banana", "appetite"]
        for word in words:
            bookmark = Bookmark(
                id=None,
                word=word,
                definition=f"Definition of {word}",
                part_of_speech="noun",
                phonetic=None,
                synonyms="",
                antonyms="",
                example=None,
                added_at=datetime.now(),
                updated_at=datetime.now(),
            )
            repository.add(bookmark=bookmark)

        results = repository.search(query="app")

        assert len(results) == 3
        words_found = [r.word for r in results]
        assert "apple" in words_found
        assert "application" in words_found
        assert "appetite" in words_found
        assert "banana" not in words_found

    def test_delete(self, repository: BookmarkRepository, sample_bookmark: Bookmark) -> None:
        """Test deleting a bookmark."""
        repository.add(bookmark=sample_bookmark)
        assert repository.exists(word="hello")

        result = repository.delete(word="hello")

        assert result is True
        assert not repository.exists(word="hello")

    def test_delete_not_found(self, repository: BookmarkRepository) -> None:
        """Test deleting non-existent bookmark."""
        result = repository.delete(word="nonexistent")
        assert result is False

    def test_count(self, repository: BookmarkRepository, sample_bookmark: Bookmark) -> None:
        """Test counting bookmarks."""
        assert repository.count() == 0

        repository.add(bookmark=sample_bookmark)
        assert repository.count() == 1

    def test_clear(self, repository: BookmarkRepository) -> None:
        """Test clearing all bookmarks."""
        for i in range(3):
            bookmark = Bookmark(
                id=None,
                word=f"word{i}",
                definition=f"Definition {i}",
                part_of_speech="noun",
                phonetic=None,
                synonyms="",
                antonyms="",
                example=None,
                added_at=datetime.now(),
                updated_at=datetime.now(),
            )
            repository.add(bookmark=bookmark)

        assert repository.count() == 3

        deleted = repository.clear()

        assert deleted == 3
        assert repository.count() == 0


class TestBookmarkManager:
    """Tests for BookmarkManager class."""

    @pytest.fixture
    def manager(self, temp_db_path: Path) -> Generator[BookmarkManager, None, None]:
        """Create a test manager."""
        mgr = BookmarkManager(db_path=temp_db_path)
        yield mgr
        mgr.close()
        temp_db_path.unlink(missing_ok=True)

    @pytest.fixture
    def sample_word(self) -> Word:
        """Create a sample Word for testing."""
        return Word.from_api_response(
            data=[
                {
                    "word": "test",
                    "phonetics": [{"text": "/test/"}],
                    "meanings": [
                        {
                            "partOfSpeech": "noun",
                            "definitions": [
                                {
                                    "definition": "A procedure",
                                    "synonyms": ["exam"],
                                    "antonyms": [],
                                }
                            ],
                            "synonyms": [],
                            "antonyms": [],
                        }
                    ],
                    "sourceUrls": [],
                }
            ]
        )

    def test_add_word(self, manager: BookmarkManager, sample_word: Word) -> None:
        """Test adding a word to bookmarks."""
        result = manager.add_word(word=sample_word)

        assert result.word == "test"
        assert result.definition == "A procedure"

    def test_get(self, manager: BookmarkManager, sample_word: Word) -> None:
        """Test getting a bookmark."""
        manager.add_word(word=sample_word)

        result = manager.get(word="test")

        assert result.word == "test"

    def test_exists(self, manager: BookmarkManager, sample_word: Word) -> None:
        """Test checking if word is bookmarked."""
        assert not manager.exists(word="test")

        manager.add_word(word=sample_word)

        assert manager.exists(word="test")

    def test_context_manager(self, temp_db_path: Path, sample_word: Word) -> None:
        """Test manager as context manager."""
        with BookmarkManager(db_path=temp_db_path) as manager:
            manager.add_word(word=sample_word)
            assert manager.exists(word="test")

        temp_db_path.unlink(missing_ok=True)

    def test_add_bookmark(self, manager: BookmarkManager) -> None:
        """Test adding a bookmark model directly."""
        bookmark = Bookmark(
            id=None,
            word="manual",
            definition="Added directly",
            part_of_speech="adjective",
            phonetic=None,
            synonyms="",
            antonyms="",
            example=None,
            added_at=datetime.now(),
            updated_at=datetime.now(),
        )

        result = manager.add_bookmark(bookmark=bookmark)
        assert result.id is not None
        assert manager.exists(word="manual")

    def test_proxy_methods(self, manager: BookmarkManager, sample_word: Word) -> None:
        """Test list/search/delete/count/clear proxy behavior."""
        manager.add_word(word=sample_word)

        assert manager.count() == 1

        listed = manager.list_all(limit=10, offset=0)
        assert len(listed) == 1
        assert listed[0].word == "test"

        searched = manager.search(query="te", limit=10)
        assert len(searched) == 1
        assert searched[0].word == "test"

        assert manager.delete(word="test") is True
        assert manager.count() == 0

        manager.add_word(word=sample_word)
        deleted = manager.clear()
        assert deleted == 1
        assert manager.count() == 0
