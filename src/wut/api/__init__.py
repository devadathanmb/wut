"""Dictionary API client module."""

from wut.api.dictionary import DictionaryAPIError, DictionaryClient, WordNotFoundError

__all__ = ["DictionaryClient", "DictionaryAPIError", "WordNotFoundError"]
