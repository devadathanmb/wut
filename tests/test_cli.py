"""Tests for CLI commands."""

from datetime import datetime
from typing import Any, cast
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from wut.api.dictionary import APIConnectionError, APITimeoutError, WordNotFoundError
from wut.audio.pronunciation import PronunciationError
from wut.cli import Context, _add_bookmark, _play_pronunciation, main
from wut.cli import pronounce as pronounce_command
from wut.core.bookmarks import BookmarkExistsError, BookmarkNotFoundError
from wut.core.models import Bookmark, Word


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def sample_word() -> Word:
    """Create a sample Word for testing."""
    return Word.from_api_response(
        data=[
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
            mock_client.lookup.side_effect = WordNotFoundError(word="xyzabc")
            MockClient.return_value = mock_client

            result = runner.invoke(main, ["xyzabc"])

            assert result.exit_code == 1
            assert "not found" in result.output.lower()

    def test_lookup_timeout_error(self, runner: CliRunner) -> None:
        """Test lookup timeout error handling."""
        with patch("wut.cli.DictionaryClient") as MockClient:
            mock_client = MagicMock()
            mock_client.lookup.side_effect = APITimeoutError("timeout")
            MockClient.return_value = mock_client

            result = runner.invoke(main, ["hello"])

            assert result.exit_code == 1
            assert "timed out" in result.output.lower()

    def test_lookup_connection_error(self, runner: CliRunner) -> None:
        """Test lookup connection error handling."""
        with patch("wut.cli.DictionaryClient") as MockClient:
            mock_client = MagicMock()
            mock_client.lookup.side_effect = APIConnectionError("offline")
            MockClient.return_value = mock_client

            result = runner.invoke(main, ["hello"])

            assert result.exit_code == 1
            assert "internet connection" in result.output.lower()

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

    def test_bookmark_show_not_found(self, runner: CliRunner) -> None:
        """Test showing a missing bookmark."""
        with patch("wut.cli.BookmarkManager") as MockManager:
            mock_manager = MagicMock()
            mock_manager.get.side_effect = BookmarkNotFoundError(word="missing")
            MockManager.return_value = mock_manager

            result = runner.invoke(main, ["bookmark", "show", "missing"])

            assert result.exit_code == 1
            assert "not bookmarked" in result.output.lower()

    def test_bookmark_add_success(self, runner: CliRunner, sample_word: Word) -> None:
        """Test bookmark add command success path."""
        with (
            patch("wut.cli.DictionaryClient") as MockClient,
            patch("wut.cli.BookmarkManager") as MockManager,
        ):
            mock_client = MagicMock()
            mock_client.lookup.return_value = sample_word
            MockClient.return_value = mock_client

            mock_manager = MagicMock()
            MockManager.return_value = mock_manager

            result = runner.invoke(main, ["bookmark", "add", "hello"])

            assert result.exit_code == 0
            assert "bookmarked" in result.output.lower()
            mock_manager.add_word.assert_called_once_with(word=sample_word)

    def test_bookmark_add_word_not_found(self, runner: CliRunner) -> None:
        """Test bookmark add with missing word."""
        with patch("wut.cli.DictionaryClient") as MockClient:
            mock_client = MagicMock()
            mock_client.lookup.side_effect = WordNotFoundError(word="missing")
            MockClient.return_value = mock_client

            result = runner.invoke(main, ["bookmark", "add", "missing"])

            assert result.exit_code == 1
            assert "not found" in result.output.lower()

    def test_bookmark_add_api_error(self, runner: CliRunner) -> None:
        """Test bookmark add shows API error message."""
        with patch("wut.cli.DictionaryClient") as MockClient:
            mock_client = MagicMock()
            mock_client.lookup.side_effect = APITimeoutError("upstream timed out")
            MockClient.return_value = mock_client

            result = runner.invoke(main, ["bookmark", "add", "hello"])

            assert result.exit_code == 1
            assert "upstream timed out" in result.output.lower()

    def test_bookmark_add_duplicate(self, runner: CliRunner, sample_word: Word) -> None:
        """Test bookmark add duplicate warning path."""
        with (
            patch("wut.cli.DictionaryClient") as MockClient,
            patch("wut.cli.BookmarkManager") as MockManager,
        ):
            mock_client = MagicMock()
            mock_client.lookup.return_value = sample_word
            MockClient.return_value = mock_client

            mock_manager = MagicMock()
            mock_manager.add_word.side_effect = BookmarkExistsError(word="hello")
            MockManager.return_value = mock_manager

            result = runner.invoke(main, ["bookmark", "add", "hello"])

            assert result.exit_code == 0
            assert "already bookmarked" in result.output.lower()

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

    def test_bookmark_delete_cancelled(self, runner: CliRunner) -> None:
        """Test deletion cancellation when confirmation is declined."""
        with (
            patch("wut.cli.BookmarkManager") as MockManager,
            patch("wut.cli.Confirm.ask", return_value=False),
        ):
            mock_manager = MagicMock()
            mock_manager.exists.return_value = True
            MockManager.return_value = mock_manager

            result = runner.invoke(main, ["bookmark", "delete", "hello"])

            assert result.exit_code == 0
            assert "cancelled" in result.output.lower()
            mock_manager.delete.assert_not_called()

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

    def test_bookmark_clear_empty(self, runner: CliRunner) -> None:
        """Test clear when there are no bookmarks."""
        with patch("wut.cli.BookmarkManager") as MockManager:
            mock_manager = MagicMock()
            mock_manager.count.return_value = 0
            MockManager.return_value = mock_manager

            result = runner.invoke(main, ["bookmark", "clear"])

            assert result.exit_code == 0
            assert "no bookmarks to delete" in result.output.lower()
            mock_manager.clear.assert_not_called()

    def test_bookmark_clear_cancelled(self, runner: CliRunner) -> None:
        """Test clear cancellation when confirmation is declined."""
        with (
            patch("wut.cli.BookmarkManager") as MockManager,
            patch("wut.cli.Confirm.ask", return_value=False),
        ):
            mock_manager = MagicMock()
            mock_manager.count.return_value = 3
            MockManager.return_value = mock_manager

            result = runner.invoke(main, ["bookmark", "clear"])

            assert result.exit_code == 0
            assert "cancelled" in result.output.lower()
            mock_manager.clear.assert_not_called()


class TestPronounceCommand:
    """Tests for pronounce command."""

    def test_pronounce_success(self, runner: CliRunner) -> None:
        """Test pronounce command success and cleanup."""
        with patch("wut.cli.PronunciationPlayer") as MockPlayer:
            mock_player = MagicMock()
            MockPlayer.return_value = mock_player

            result = runner.invoke(main, ["pronounce", "hello"])

            assert result.exit_code == 0
            mock_player.play.assert_called_once_with(word="hello", block=True)
            mock_player.close.assert_called_once()

    def test_pronounce_error(self, runner: CliRunner) -> None:
        """Test pronounce command error path."""
        with patch("wut.cli.PronunciationPlayer") as MockPlayer:
            mock_player = MagicMock()
            mock_player.play.side_effect = PronunciationError("speaker unavailable")
            MockPlayer.return_value = mock_player

            result = runner.invoke(main, ["pronounce", "hello"])

            assert result.exit_code == 1
            assert "could not play pronunciation" in result.output.lower()
            mock_player.close.assert_called_once()

    def test_pronounce_interactive_repeat(self) -> None:
        """Test repeat loop when interactive context is enabled."""
        ctx = Context()
        ctx.interactive = True

        with (
            patch("wut.cli.PronunciationPlayer") as MockPlayer,
            patch("wut.cli.Confirm.ask", side_effect=[True, False]),
        ):
            mock_player = MagicMock()
            MockPlayer.return_value = mock_player

            callback = pronounce_command.callback
            assert callback is not None
            cast_callback = callback.__wrapped__ if hasattr(callback, "__wrapped__") else callback
            cast_callback = cast(Any, cast_callback)
            cast_callback(ctx, word="hello", slow=False)

            assert mock_player.play.call_count == 2
            mock_player.close.assert_called_once()


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


class TestContext:
    """Tests for CLI context dependency management."""

    def test_getters_are_lazy_singletons(self) -> None:
        """Test lazy initialization and singleton behavior for dependencies."""
        ctx = Context()

        with (
            patch("wut.cli.BookmarkManager") as MockManager,
            patch("wut.cli.DictionaryClient") as MockClient,
            patch("wut.cli.PronunciationPlayer") as MockPlayer,
        ):
            manager1 = ctx.get_bookmark_manager()
            manager2 = ctx.get_bookmark_manager()
            client1 = ctx.get_dictionary_client()
            client2 = ctx.get_dictionary_client()
            player1 = ctx.get_pronunciation_player()
            player2 = ctx.get_pronunciation_player()

            assert manager1 is manager2
            assert client1 is client2
            assert player1 is player2
            MockManager.assert_called_once()
            MockClient.assert_called_once()
            MockPlayer.assert_called_once()

    def test_cleanup_closes_initialized_dependencies(self) -> None:
        """Test cleanup only closes resources that were initialized."""
        ctx = Context()
        ctx.bookmark_manager = MagicMock()
        ctx.dictionary_client = None
        ctx.pronunciation_player = MagicMock()

        ctx.cleanup()

        ctx.bookmark_manager.close.assert_called_once()
        assert ctx.dictionary_client is None
        ctx.pronunciation_player.close.assert_called_once()


class TestCliHelpers:
    """Tests for helper functions used by CLI commands."""

    def test_play_pronunciation_success(self) -> None:
        """Play helper should invoke player in blocking mode."""
        ctx = Context()
        player = MagicMock()
        ctx.pronunciation_player = player

        _play_pronunciation(ctx=ctx, word="hello")

        player.play.assert_called_once_with(word="hello", block=True)

    def test_play_pronunciation_warns_on_error(self) -> None:
        """Play helper should convert pronunciation errors to warnings."""
        ctx = Context()
        player = MagicMock()
        player.play.side_effect = PronunciationError("audio backend failed")
        ctx.pronunciation_player = player

        with patch("wut.cli.formatter.display_warning") as mock_warning:
            _play_pronunciation(ctx=ctx, word="hello")

        mock_warning.assert_called_once()
        assert "could not play pronunciation" in mock_warning.call_args.kwargs["message"].lower()

    def test_add_bookmark_success(self, sample_word: Word) -> None:
        """Bookmark helper should add word and show success."""
        ctx = Context()
        manager = MagicMock()
        ctx.bookmark_manager = manager

        with patch("wut.cli.formatter.display_success") as mock_success:
            _add_bookmark(ctx=ctx, word_result=sample_word)

        manager.add_word.assert_called_once_with(word=sample_word)
        mock_success.assert_called_once()
        assert "bookmarked" in mock_success.call_args.kwargs["message"].lower()

    def test_add_bookmark_duplicate_warns(self, sample_word: Word) -> None:
        """Bookmark helper should show warning on duplicate bookmark."""
        ctx = Context()
        manager = MagicMock()
        manager.add_word.side_effect = BookmarkExistsError(word=sample_word.word)
        ctx.bookmark_manager = manager

        with patch("wut.cli.formatter.display_warning") as mock_warning:
            _add_bookmark(ctx=ctx, word_result=sample_word)

        mock_warning.assert_called_once()
        assert "already bookmarked" in mock_warning.call_args.kwargs["message"].lower()
