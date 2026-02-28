"""Domain models for dictionary data."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Self


@dataclass(frozen=True, slots=True)
class Phonetic:
    """Phonetic representation of a word."""

    text: str
    audio_url: str | None = None
    source_url: str | None = None

    @classmethod
    def from_api_response(cls, data: Mapping[str, str | None]) -> Self:
        """Create Phonetic from API response dict."""
        return cls(
            text=data.get("text") or "",
            audio_url=data.get("audio"),
            source_url=data.get("sourceUrl"),
        )


@dataclass(frozen=True, slots=True)
class Definition:
    """A single definition of a word."""

    text: str
    example: str | None = None
    synonyms: tuple[str, ...] = field(default_factory=tuple)
    antonyms: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_api_response(cls, data: Mapping[str, Any]) -> Self:
        """Create Definition from API response dict."""
        return cls(
            text=data.get("definition", ""),
            example=data.get("example"),
            synonyms=tuple(data.get("synonyms", [])),
            antonyms=tuple(data.get("antonyms", [])),
        )


@dataclass(frozen=True, slots=True)
class Meaning:
    """A meaning of a word with its part of speech and definitions."""

    part_of_speech: str
    definitions: tuple[Definition, ...]
    synonyms: tuple[str, ...] = field(default_factory=tuple)
    antonyms: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_api_response(cls, data: Mapping[str, Any]) -> Self:
        """Create Meaning from API response dict."""
        definitions = tuple(
            Definition.from_api_response(data=d) for d in data.get("definitions", [])
        )
        return cls(
            part_of_speech=data.get("partOfSpeech", ""),
            definitions=definitions,
            synonyms=tuple(data.get("synonyms", [])),
            antonyms=tuple(data.get("antonyms", [])),
        )

    @property
    def all_synonyms(self) -> tuple[str, ...]:
        """Get all synonyms including from definitions."""
        synonyms = set(self.synonyms)
        for definition in self.definitions:
            synonyms.update(definition.synonyms)
        return tuple(sorted(synonyms))

    @property
    def all_antonyms(self) -> tuple[str, ...]:
        """Get all antonyms including from definitions."""
        antonyms = set(self.antonyms)
        for definition in self.definitions:
            antonyms.update(definition.antonyms)
        return tuple(sorted(antonyms))


@dataclass(frozen=True, slots=True)
class Word:
    """Complete word entry from the dictionary."""

    word: str
    phonetics: tuple[Phonetic, ...]
    meanings: tuple[Meaning, ...]
    source_urls: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_api_response(cls, data: list[dict[str, Any]]) -> Self:
        """Create Word from API response (list of entries)."""
        if not data:
            raise ValueError("Empty API response")

        # Combine all entries for the same word
        first_entry = data[0]
        word_text = first_entry.get("word", "")

        # Collect all phonetics
        phonetics: list[Phonetic] = []
        for entry in data:
            for phonetic_data in entry.get("phonetics", []):
                if phonetic_data.get("text"):
                    phonetics.append(Phonetic.from_api_response(data=phonetic_data))

        # Collect all meanings
        meanings: list[Meaning] = []
        for entry in data:
            for meaning_data in entry.get("meanings", []):
                meanings.append(Meaning.from_api_response(data=meaning_data))

        # Collect source URLs
        source_urls: list[str] = []
        for entry in data:
            source_urls.extend(entry.get("sourceUrls", []))

        return cls(
            word=word_text,
            phonetics=tuple(phonetics),
            meanings=tuple(meanings),
            source_urls=tuple(source_urls),
        )

    @property
    def ipa(self) -> str | None:
        """Get the first available IPA phonetic."""
        for phonetic in self.phonetics:
            if phonetic.text:
                return phonetic.text
        return None

    @property
    def audio_url(self) -> str | None:
        """Get the first available audio URL."""
        for phonetic in self.phonetics:
            if phonetic.audio_url:
                return phonetic.audio_url
        return None

    @property
    def all_synonyms(self) -> tuple[str, ...]:
        """Get all synonyms from all meanings."""
        synonyms: set[str] = set()
        for meaning in self.meanings:
            synonyms.update(meaning.all_synonyms)
        return tuple(sorted(synonyms))

    @property
    def all_antonyms(self) -> tuple[str, ...]:
        """Get all antonyms from all meanings."""
        antonyms: set[str] = set()
        for meaning in self.meanings:
            antonyms.update(meaning.all_antonyms)
        return tuple(sorted(antonyms))


@dataclass(slots=True)
class Bookmark:
    """A bookmarked word with its definition."""

    id: int | None
    word: str
    definition: str
    part_of_speech: str
    phonetic: str | None
    synonyms: str  # Comma-separated
    antonyms: str  # Comma-separated
    example: str | None
    added_at: datetime
    updated_at: datetime

    @classmethod
    def from_word(cls, word: Word) -> Self:
        """Create a Bookmark from a Word object."""
        # Get primary definition
        primary_meaning = word.meanings[0] if word.meanings else None
        primary_definition = (
            primary_meaning.definitions[0]
            if primary_meaning and primary_meaning.definitions
            else None
        )

        return cls(
            id=None,
            word=word.word,
            definition=primary_definition.text if primary_definition else "",
            part_of_speech=primary_meaning.part_of_speech if primary_meaning else "",
            phonetic=word.ipa,
            synonyms=",".join(word.all_synonyms[:10]),  # Limit to 10
            antonyms=",".join(word.all_antonyms[:10]),
            example=primary_definition.example if primary_definition else None,
            added_at=datetime.now(),
            updated_at=datetime.now(),
        )

    @property
    def synonym_list(self) -> list[str]:
        """Get synonyms as a list."""
        return [s.strip() for s in self.synonyms.split(",") if s.strip()]

    @property
    def antonym_list(self) -> list[str]:
        """Get antonyms as a list."""
        return [a.strip() for a in self.antonyms.split(",") if a.strip()]
