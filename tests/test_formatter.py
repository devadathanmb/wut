"""Tests for Rich display formatter."""

from datetime import datetime
from io import StringIO

from rich.console import Console

from wut.core.models import Bookmark, Word
from wut.display.formatter import WordFormatter


def _make_formatter() -> tuple[WordFormatter, StringIO]:
    """Create a formatter with a test console and capture buffer."""
    buffer = StringIO()
    console = Console(file=buffer, width=120, force_terminal=False, color_system=None)
    return WordFormatter(console=console), buffer


def _sample_word(*, include_synonyms: bool = True) -> Word:
    """Create a sample word with configurable synonym/antonym presence."""
    synonyms = [f"syn{i}" for i in range(11)] if include_synonyms else []
    antonyms = [f"ant{i}" for i in range(11)] if include_synonyms else []
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
                                "synonyms": synonyms,
                                "antonyms": antonyms,
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


def _sample_bookmark(*, with_optional_fields: bool) -> Bookmark:
    """Create a bookmark with or without optional presentation fields."""
    return Bookmark(
        id=1,
        word="hello",
        definition="Used as a greeting",
        part_of_speech="interjection" if with_optional_fields else "",
        phonetic="/həˈloʊ/" if with_optional_fields else None,
        synonyms="hi,hey" if with_optional_fields else "",
        antonyms="goodbye" if with_optional_fields else "",
        example="Hello there!" if with_optional_fields else None,
        added_at=datetime(2024, 1, 2, 12, 0, 0),
        updated_at=datetime(2024, 1, 2, 12, 0, 0),
    )


def test_display_word_with_synonyms_antonyms_truncation() -> None:
    """Display word output includes header, definition, and truncation hint."""
    formatter, buffer = _make_formatter()
    formatter.display_word(word=_sample_word(include_synonyms=True))
    output = buffer.getvalue().lower()

    assert "hello" in output
    assert "/həˈloʊ/" in output
    assert "used as a greeting" in output
    assert "synonyms & antonyms" in output
    assert "(+1 more)" in output


def test_display_word_without_syn_ant_table_when_empty() -> None:
    """Do not render synonyms/antonyms table when lists are empty."""
    formatter, buffer = _make_formatter()
    formatter.display_word(word=_sample_word(include_synonyms=False))
    output = buffer.getvalue().lower()

    assert "hello" in output
    assert "definitions" in output
    assert "synonyms & antonyms" not in output


def test_display_bookmark_with_optional_fields() -> None:
    """Display bookmark includes optional details when provided."""
    formatter, buffer = _make_formatter()
    formatter.display_bookmark(bookmark=_sample_bookmark(with_optional_fields=True))
    output = buffer.getvalue().lower()

    assert "hello" in output
    assert "/həˈloʊ/" in output
    assert "interjection" in output
    assert "example:" in output
    assert "synonyms:" in output
    assert "antonyms:" in output


def test_display_bookmark_without_optional_fields() -> None:
    """Display bookmark omits optional sections when values are missing."""
    formatter, buffer = _make_formatter()
    formatter.display_bookmark(bookmark=_sample_bookmark(with_optional_fields=False))
    output = buffer.getvalue().lower()

    assert "hello" in output
    assert "used as a greeting" in output
    assert "example:" not in output
    assert "synonyms:" not in output
    assert "antonyms:" not in output


def test_display_bookmark_list_empty() -> None:
    """Display empty-state message for bookmark list."""
    formatter, buffer = _make_formatter()
    formatter.display_bookmark_list(bookmarks=[])

    assert "no bookmarks found" in buffer.getvalue().lower()


def test_display_bookmark_list_truncates_and_hides_count() -> None:
    """Truncate long definition and suppress count when requested."""
    formatter, buffer = _make_formatter()
    bookmark = Bookmark(
        id=1,
        word="hello",
        definition="x" * 80,
        part_of_speech="interjection",
        phonetic=None,
        synonyms="",
        antonyms="",
        example=None,
        added_at=datetime(2024, 1, 2, 12, 0, 0),
        updated_at=datetime(2024, 1, 2, 12, 0, 0),
    )

    formatter.display_bookmark_list(bookmarks=[bookmark], show_count=False)
    output = buffer.getvalue().lower()

    assert "bookmarked words" in output
    assert "..." in output
    assert "total:" not in output


def test_message_helpers() -> None:
    """Display helper methods print their messages."""
    formatter, buffer = _make_formatter()
    formatter.display_error(message="bad request")
    formatter.display_success(message="saved")
    formatter.display_warning(message="careful")
    formatter.display_info(message="heads up")

    output = buffer.getvalue().lower()
    assert "error:" in output
    assert "bad request" in output
    assert "saved" in output
    assert "careful" in output
    assert "heads up" in output
