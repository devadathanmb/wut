"""Dictionary API client using the Free Dictionary API."""

import httpx

from wut import __version__
from wut.core.models import Word

API_BASE_URL = "https://api.dictionaryapi.dev/api/v2/entries/en"
DEFAULT_TIMEOUT = 10.0


class DictionaryAPIError(Exception):
    """Base exception for Dictionary API errors."""


class WordNotFoundError(DictionaryAPIError):
    """Raised when a word is not found in the dictionary."""

    def __init__(self, word: str) -> None:
        self.word = word
        super().__init__(f"Word not found: '{word}'")


class APIConnectionError(DictionaryAPIError):
    """Raised when connection to API fails."""


class APITimeoutError(DictionaryAPIError):
    """Raised when API request times out."""


class DictionaryClient:
    """Client for the Free Dictionary API."""

    def __init__(
        self,
        *,
        base_url: str = API_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize dictionary client.

        Args:
            base_url: API base URL.
            timeout: Request timeout in seconds.
        """
        self._base_url = base_url
        self._timeout = timeout
        self._client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                timeout=self._timeout,
                headers={"User-Agent": f"wut-dictionary-cli/{__version__}"},
            )
        return self._client

    def lookup(self, word: str) -> Word:
        """Look up a word in the dictionary.

        Args:
            word: Word to look up.

        Returns:
            Word object with definitions.

        Raises:
            WordNotFoundError: If word not found.
            APIConnectionError: If connection fails.
            APITimeoutError: If request times out.
        """
        word = word.strip().lower()
        if not word:
            raise ValueError("Word cannot be empty")

        client = self._get_client()
        url = f"{self._base_url}/{word}"

        try:
            response = client.get(url=url)
        except httpx.TimeoutException as e:
            raise APITimeoutError(f"Request timed out: {e}") from e
        except httpx.ConnectError as e:
            raise APIConnectionError(f"Connection failed: {e}") from e
        except httpx.HTTPError as e:
            raise DictionaryAPIError(f"HTTP error: {e}") from e

        if response.status_code == 404:
            raise WordNotFoundError(word=word)

        if response.status_code >= 400:
            raise DictionaryAPIError(f"API error: {response.status_code} - {response.text}")

        try:
            data = response.json()
            return Word.from_api_response(data=data)
        except (ValueError, KeyError) as e:
            raise DictionaryAPIError(f"Failed to parse API response: {e}") from e

    def close(self) -> None:
        """Close HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "DictionaryClient":
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


# Convenience function for one-off lookups
def lookup_word(word: str, *, timeout: float = DEFAULT_TIMEOUT) -> Word:
    """Look up a word in the dictionary.

    Args:
        word: Word to look up.
        timeout: Request timeout in seconds.

    Returns:
        Word object with definitions.
    """
    with DictionaryClient(timeout=timeout) as client:
        return client.lookup(word)
