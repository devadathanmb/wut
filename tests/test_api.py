"""Tests for Dictionary API client."""

from unittest.mock import Mock, patch

import httpx
import pytest

from wut.api.dictionary import (
    APIConnectionError,
    APITimeoutError,
    DictionaryAPIError,
    DictionaryClient,
    WordNotFoundError,
    lookup_word,
)


@pytest.fixture
def sample_api_response() -> list[dict[str, object]]:
    """Sample API response."""
    return [
        {
            "word": "hello",
            "phonetics": [{"text": "/həˈloʊ/", "audio": ""}],
            "meanings": [
                {
                    "partOfSpeech": "interjection",
                    "definitions": [
                        {
                            "definition": "Used as a greeting",
                            "example": "Hello there!",
                            "synonyms": ["hi"],
                            "antonyms": [],
                        }
                    ],
                    "synonyms": [],
                    "antonyms": [],
                }
            ],
            "sourceUrls": ["https://en.wiktionary.org/wiki/hello"],
        }
    ]


class TestDictionaryClient:
    """Tests for DictionaryClient class."""

    def test_lookup_success(self, sample_api_response: list[dict[str, object]]) -> None:
        """Test successful word lookup."""
        with patch.object(httpx.Client, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_api_response
            mock_get.return_value = mock_response

            client = DictionaryClient()
            result = client.lookup("hello")

            assert result.word == "hello"
            assert len(result.meanings) == 1
            client.close()

    def test_lookup_word_not_found(self) -> None:
        """Test lookup of non-existent word."""
        with patch.object(httpx.Client, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response

            client = DictionaryClient()

            with pytest.raises(WordNotFoundError) as exc_info:
                client.lookup("xyznonexistent")

            assert exc_info.value.word == "xyznonexistent"
            client.close()

    def test_lookup_empty_word(self) -> None:
        """Test lookup with empty word."""
        client = DictionaryClient()

        with pytest.raises(ValueError, match="Word cannot be empty"):
            client.lookup("")

        with pytest.raises(ValueError, match="Word cannot be empty"):
            client.lookup("   ")

        client.close()

    def test_lookup_strips_and_lowercases(
        self, sample_api_response: list[dict[str, object]]
    ) -> None:
        """Test that word is stripped and lowercased."""
        with patch.object(httpx.Client, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_api_response
            mock_get.return_value = mock_response

            client = DictionaryClient()
            client.lookup("  HELLO  ")

            # Check that the URL was called with lowercase
            mock_get.assert_called_once()
            call_url = mock_get.call_args[0][0]
            assert "hello" in call_url
            client.close()

    def test_lookup_timeout(self) -> None:
        """Test handling of timeout."""
        with patch.object(httpx.Client, "get") as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Connection timed out")

            client = DictionaryClient()

            with pytest.raises(APITimeoutError):
                client.lookup("hello")

            client.close()

    def test_lookup_connection_error(self) -> None:
        """Test handling of connection error."""
        with patch.object(httpx.Client, "get") as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection refused")

            client = DictionaryClient()

            with pytest.raises(APIConnectionError):
                client.lookup("hello")

            client.close()

    def test_lookup_server_error(self) -> None:
        """Test handling of server error."""
        with patch.object(httpx.Client, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_get.return_value = mock_response

            client = DictionaryClient()

            with pytest.raises(DictionaryAPIError):
                client.lookup("hello")

            client.close()

    def test_context_manager(self, sample_api_response: list[dict[str, object]]) -> None:
        """Test client as context manager."""
        with patch.object(httpx.Client, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_api_response
            mock_get.return_value = mock_response

            with DictionaryClient() as client:
                result = client.lookup("hello")
                assert result.word == "hello"


class TestLookupWordFunction:
    """Tests for lookup_word convenience function."""

    def test_lookup_word(self, sample_api_response: list[dict[str, object]]) -> None:
        """Test the convenience function."""
        with patch.object(httpx.Client, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_api_response
            mock_get.return_value = mock_response

            result = lookup_word("hello")

            assert result.word == "hello"
