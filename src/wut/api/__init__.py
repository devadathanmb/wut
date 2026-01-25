"""Dictionary API client module."""

from wut.api.dictionary import DictionaryClient, DictionaryAPIError, WordNotFoundError

__all__ = ["DictionaryClient", "DictionaryAPIError", "WordNotFoundError"]
