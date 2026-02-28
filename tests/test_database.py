"""Tests for database and bookmark operations."""

import tempfile
from collections.abc import Generator
from datetime import datetime
from pathlib import Path

import pytest

from wut.core.bookmarks import BookmarkManager
from wut.core.database import (
    BookmarkExistsError,
    BookmarkNotFoundError,
    BookmarkRepository,
    Database,
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
    return BookmarkRepository(database)


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


class TestBookmarkRepository:
    """Tests for BookmarkRepository class."""

    def test_add_bookmark(self, repository: BookmarkRepository, sample_bookmark: Bookmark) -> None:
        """Test adding a bookmark."""
        result = repository.add(sample_bookmark)

        assert result.id is not None
        assert result.word == "hello"

    def test_add_duplicate_raises(
        self, repository: BookmarkRepository, sample_bookmark: Bookmark
    ) -> None:
        """Test that adding duplicate raises error."""
        repository.add(sample_bookmark)

        with pytest.raises(BookmarkExistsError) as exc_info:
            repository.add(sample_bookmark)

        assert exc_info.value.word == "hello"

    def test_get_bookmark(self, repository: BookmarkRepository, sample_bookmark: Bookmark) -> None:
        """Test retrieving a bookmark."""
        repository.add(sample_bookmark)

        result = repository.get("hello")

        assert result.word == "hello"
        assert result.definition == "A greeting"
        assert result.phonetic == "/həˈloʊ/"

    def test_get_case_insensitive(
        self, repository: BookmarkRepository, sample_bookmark: Bookmark
    ) -> None:
        """Test that get is case insensitive."""
        repository.add(sample_bookmark)

        result = repository.get("HELLO")
        assert result.word == "hello"

    def test_get_not_found_raises(self, repository: BookmarkRepository) -> None:
        """Test that getting non-existent bookmark raises error."""
        with pytest.raises(BookmarkNotFoundError) as exc_info:
            repository.get("nonexistent")

        assert exc_info.value.word == "nonexistent"

    def test_exists(self, repository: BookmarkRepository, sample_bookmark: Bookmark) -> None:
        """Test checking if bookmark exists."""
        assert not repository.exists("hello")

        repository.add(sample_bookmark)

        assert repository.exists("hello")
        assert repository.exists("HELLO")  # Case insensitive

    def test_list_all(self, repository: BookmarkRepository, sample_bookmark: Bookmark) -> None:
        """Test listing all bookmarks."""
        # Add multiple bookmarks
        repository.add(sample_bookmark)

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
        repository.add(bookmark2)

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
            repository.add(bookmark)

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
            repository.add(bookmark)

        results = repository.search("app")

        assert len(results) == 3
        words_found = [r.word for r in results]
        assert "apple" in words_found
        assert "application" in words_found
        assert "appetite" in words_found
        assert "banana" not in words_found

    def test_delete(self, repository: BookmarkRepository, sample_bookmark: Bookmark) -> None:
        """Test deleting a bookmark."""
        repository.add(sample_bookmark)
        assert repository.exists("hello")

        result = repository.delete("hello")

        assert result is True
        assert not repository.exists("hello")

    def test_delete_not_found(self, repository: BookmarkRepository) -> None:
        """Test deleting non-existent bookmark."""
        result = repository.delete("nonexistent")
        assert result is False

    def test_count(self, repository: BookmarkRepository, sample_bookmark: Bookmark) -> None:
        """Test counting bookmarks."""
        assert repository.count() == 0

        repository.add(sample_bookmark)
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
            repository.add(bookmark)

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
            [
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
        result = manager.add_word(sample_word)

        assert result.word == "test"
        assert result.definition == "A procedure"

    def test_get(self, manager: BookmarkManager, sample_word: Word) -> None:
        """Test getting a bookmark."""
        manager.add_word(sample_word)

        result = manager.get("test")

        assert result.word == "test"

    def test_exists(self, manager: BookmarkManager, sample_word: Word) -> None:
        """Test checking if word is bookmarked."""
        assert not manager.exists("test")

        manager.add_word(sample_word)

        assert manager.exists("test")

    def test_context_manager(self, temp_db_path: Path, sample_word: Word) -> None:
        """Test manager as context manager."""
        with BookmarkManager(db_path=temp_db_path) as manager:
            manager.add_word(sample_word)
            assert manager.exists("test")

        temp_db_path.unlink(missing_ok=True)
