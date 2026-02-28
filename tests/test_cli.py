"""Tests for CLI commands."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from wut.api.dictionary import WordNotFoundError
from wut.cli import main
from wut.core.models import Bookmark, Word


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def sample_word() -> Word:
    """Create a sample Word for testing."""
    return Word.from_api_response(
        [
            {
                "word": "hello",
                "phonetics": [{"text": "/həˈloʊ/"}],
                "meanings": [
                    {
                        "partOfSpeech": "interjection",
                        "definitions": [
                            {
                                "definition": "Used as a greeting",
                                "example": "Hello there!",
                                "synonyms": ["hi"],
                                "antonyms": ["goodbye"],
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


@pytest.fixture
def sample_bookmark() -> Bookmark:
    """Create a sample Bookmark for testing."""
    return Bookmark(
        id=1,
        word="hello",
        definition="Used as a greeting",
        part_of_speech="interjection",
        phonetic="/həˈloʊ/",
        synonyms="hi,hey",
        antonyms="goodbye",
        example="Hello there!",
        added_at=datetime.now(),
        updated_at=datetime.now(),
    )


class TestMainCommand:
    """Tests for main CLI command."""

    def test_help(self, runner: CliRunner) -> None:
        """Test help output."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Wut?" in result.output
        assert "dictionary" in result.output.lower()

    def test_version(self, runner: CliRunner) -> None:
        """Test version output."""
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "wut" in result.output.lower()

    def test_no_args_shows_help(self, runner: CliRunner) -> None:
        """Test that no args shows help."""
        result = runner.invoke(main, [])
        assert result.exit_code == 0
        assert "Usage:" in result.output


class TestWordLookup:
    """Tests for word lookup (main command with word argument)."""

    def test_lookup_success(self, runner: CliRunner, sample_word: Word) -> None:
        """Test successful word lookup (non-interactive by default)."""
        with patch("wut.cli.DictionaryClient") as MockClient:
            mock_client = MagicMock()
            mock_client.lookup.return_value = sample_word
            MockClient.return_value = mock_client

            result = runner.invoke(main, ["hello"])

            assert result.exit_code == 0
            assert "hello" in result.output.lower()

    def test_lookup_word_not_found(self, runner: CliRunner) -> None:
        """Test lookup of non-existent word."""
        with patch("wut.cli.DictionaryClient") as MockClient:
            mock_client = MagicMock()
            mock_client.lookup.side_effect = WordNotFoundError("xyzabc")
            MockClient.return_value = mock_client

            result = runner.invoke(main, ["xyzabc"])

            assert result.exit_code == 1
            assert "not found" in result.output.lower()

    def test_lookup_with_pronounce_flag(self, runner: CliRunner, sample_word: Word) -> None:
        """Test lookup with -p flag plays pronunciation."""
        with (
            patch("wut.cli.DictionaryClient") as MockClient,
            patch("wut.cli._play_pronunciation") as mock_play,
        ):
            mock_client = MagicMock()
            mock_client.lookup.return_value = sample_word
            MockClient.return_value = mock_client

            result = runner.invoke(main, ["hello", "-p"])

            assert result.exit_code == 0
            assert "hello" in result.output.lower()
            mock_play.assert_called_once()

    def test_lookup_with_bookmark_flag(self, runner: CliRunner, sample_word: Word) -> None:
        """Test lookup with -b flag bookmarks the word."""
        with (
            patch("wut.cli.DictionaryClient") as MockClient,
            patch("wut.cli._add_bookmark") as mock_bookmark,
        ):
            mock_client = MagicMock()
            mock_client.lookup.return_value = sample_word
            MockClient.return_value = mock_client

            result = runner.invoke(main, ["hello", "-b"])

            assert result.exit_code == 0
            assert "hello" in result.output.lower()
            mock_bookmark.assert_called_once()

    def test_interactive_mode_prompts(self, runner: CliRunner, sample_word: Word) -> None:
        """Test interactive mode shows prompts."""
        with patch("wut.cli.DictionaryClient") as MockClient:
            mock_client = MagicMock()
            mock_client.lookup.return_value = sample_word
            MockClient.return_value = mock_client

            result = runner.invoke(main, ["hello", "-i"], input="n\nn\n")

            assert result.exit_code == 0
            assert "hello" in result.output.lower()
            assert "pronunciation" in result.output.lower()  # Prompt should appear


class TestBookmarkCommands:
    """Tests for bookmark subcommands."""

    def test_bookmark_list_empty(self, runner: CliRunner) -> None:
        """Test listing empty bookmarks."""
        with patch("wut.cli.BookmarkManager") as MockManager:
            mock_manager = MagicMock()
            mock_manager.list_all.return_value = []
            mock_manager.search.return_value = []
            MockManager.return_value = mock_manager

            result = runner.invoke(main, ["bookmark", "list"])

            assert result.exit_code == 0
            assert "no bookmarks" in result.output.lower()

    def test_bookmark_list_with_items(self, runner: CliRunner, sample_bookmark: Bookmark) -> None:
        """Test listing bookmarks."""
        with patch("wut.cli.BookmarkManager") as MockManager:
            mock_manager = MagicMock()
            mock_manager.list_all.return_value = [sample_bookmark]
            MockManager.return_value = mock_manager

            result = runner.invoke(main, ["bookmark", "list"])

            assert result.exit_code == 0
            assert "hello" in result.output.lower()

    def test_bookmark_show(self, runner: CliRunner, sample_bookmark: Bookmark) -> None:
        """Test showing a bookmark."""
        with patch("wut.cli.BookmarkManager") as MockManager:
            mock_manager = MagicMock()
            mock_manager.get.return_value = sample_bookmark
            MockManager.return_value = mock_manager

            result = runner.invoke(main, ["bookmark", "show", "hello"])

            assert result.exit_code == 0
            assert "hello" in result.output.lower()
            assert "greeting" in result.output.lower()

    def test_bookmark_delete_with_force(self, runner: CliRunner) -> None:
        """Test deleting a bookmark with force flag."""
        with patch("wut.cli.BookmarkManager") as MockManager:
            mock_manager = MagicMock()
            mock_manager.exists.return_value = True
            mock_manager.delete.return_value = True
            MockManager.return_value = mock_manager

            result = runner.invoke(main, ["bookmark", "delete", "hello", "-f"])

            assert result.exit_code == 0
            assert "deleted" in result.output.lower()

    def test_bookmark_delete_not_found(self, runner: CliRunner) -> None:
        """Test deleting non-existent bookmark."""
        with patch("wut.cli.BookmarkManager") as MockManager:
            mock_manager = MagicMock()
            mock_manager.exists.return_value = False
            MockManager.return_value = mock_manager

            result = runner.invoke(main, ["bookmark", "delete", "nonexistent"])

            assert result.exit_code == 1
            assert "not bookmarked" in result.output.lower()

    def test_bookmark_clear_with_force(self, runner: CliRunner) -> None:
        """Test clearing all bookmarks."""
        with patch("wut.cli.BookmarkManager") as MockManager:
            mock_manager = MagicMock()
            mock_manager.count.return_value = 5
            mock_manager.clear.return_value = 5
            MockManager.return_value = mock_manager

            result = runner.invoke(main, ["bookmark", "clear", "-f"])

            assert result.exit_code == 0
            assert "5" in result.output


class TestInfoCommand:
    """Tests for info command."""

    def test_info(self, runner: CliRunner) -> None:
        """Test info command."""
        with patch("wut.cli.BookmarkManager") as MockManager:
            mock_manager = MagicMock()
            mock_manager.db_path = "/tmp/test.db"
            mock_manager.count.return_value = 10
            MockManager.return_value = mock_manager

            result = runner.invoke(main, ["info"])

            assert result.exit_code == 0
            assert "wut" in result.output.lower()
            assert "10" in result.output


class TestBookmarkHelp:
    """Tests for bookmark subcommand help."""

    def test_bookmark_help(self, runner: CliRunner) -> None:
        """Test bookmark help."""
        result = runner.invoke(main, ["bookmark", "--help"])
        assert result.exit_code == 0
        assert "add" in result.output.lower()
        assert "list" in result.output.lower()
        assert "delete" in result.output.lower()
