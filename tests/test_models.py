"""Tests for data models."""

from datetime import datetime

import pytest

from wut.core.models import Bookmark, Definition, Meaning, Phonetic, Word


class TestPhonetic:
    """Tests for Phonetic model."""

    def test_from_api_response(self) -> None:
        """Test creating Phonetic from API response."""
        data = {
            "text": "/həˈloʊ/",
            "audio": "https://example.com/audio.mp3",
            "sourceUrl": "https://example.com",
        }
        phonetic = Phonetic.from_api_response(data)

        assert phonetic.text == "/həˈloʊ/"
        assert phonetic.audio_url == "https://example.com/audio.mp3"
        assert phonetic.source_url == "https://example.com"

    def test_from_api_response_missing_fields(self) -> None:
        """Test creating Phonetic with missing optional fields."""
        data: dict[str, str | None] = {"text": "/test/"}
        phonetic = Phonetic.from_api_response(data)

        assert phonetic.text == "/test/"
        assert phonetic.audio_url is None
        assert phonetic.source_url is None

    def test_from_api_response_empty(self) -> None:
        """Test creating Phonetic from empty dict."""
        phonetic = Phonetic.from_api_response({})
        assert phonetic.text == ""


class TestDefinition:
    """Tests for Definition model."""

    def test_from_api_response(self) -> None:
        """Test creating Definition from API response."""
        data = {
            "definition": "A greeting",
            "example": "Hello, world!",
            "synonyms": ["hi", "hey"],
            "antonyms": ["goodbye"],
        }
        definition = Definition.from_api_response(data)

        assert definition.text == "A greeting"
        assert definition.example == "Hello, world!"
        assert definition.synonyms == ("hi", "hey")
        assert definition.antonyms == ("goodbye",)

    def test_from_api_response_minimal(self) -> None:
        """Test creating Definition with only required fields."""
        data = {"definition": "Test definition"}
        definition = Definition.from_api_response(data)

        assert definition.text == "Test definition"
        assert definition.example is None
        assert definition.synonyms == ()
        assert definition.antonyms == ()


class TestMeaning:
    """Tests for Meaning model."""

    def test_from_api_response(self) -> None:
        """Test creating Meaning from API response."""
        data = {
            "partOfSpeech": "noun",
            "definitions": [
                {"definition": "First def", "synonyms": ["syn1"]},
                {"definition": "Second def"},
            ],
            "synonyms": ["global_syn"],
            "antonyms": ["global_ant"],
        }
        meaning = Meaning.from_api_response(data)

        assert meaning.part_of_speech == "noun"
        assert len(meaning.definitions) == 2
        assert meaning.synonyms == ("global_syn",)
        assert meaning.antonyms == ("global_ant",)

    def test_all_synonyms(self) -> None:
        """Test aggregating synonyms from definitions."""
        data = {
            "partOfSpeech": "verb",
            "definitions": [
                {"definition": "Def 1", "synonyms": ["syn1", "syn2"]},
                {"definition": "Def 2", "synonyms": ["syn3"]},
            ],
            "synonyms": ["global_syn"],
            "antonyms": [],
        }
        meaning = Meaning.from_api_response(data)

        all_syns = meaning.all_synonyms
        assert "syn1" in all_syns
        assert "syn2" in all_syns
        assert "syn3" in all_syns
        assert "global_syn" in all_syns


class TestWord:
    """Tests for Word model."""

    @pytest.fixture
    def sample_api_response(self) -> list[dict]:
        """Sample API response for testing."""
        return [
            {
                "word": "hello",
                "phonetics": [
                    {"text": "/həˈloʊ/", "audio": "https://example.com/hello.mp3"},
                ],
                "meanings": [
                    {
                        "partOfSpeech": "noun",
                        "definitions": [
                            {
                                "definition": "A greeting",
                                "example": "She said hello.",
                                "synonyms": ["greeting"],
                                "antonyms": [],
                            }
                        ],
                        "synonyms": [],
                        "antonyms": [],
                    },
                    {
                        "partOfSpeech": "interjection",
                        "definitions": [
                            {
                                "definition": "Used as a greeting",
                                "synonyms": ["hi", "hey"],
                                "antonyms": ["goodbye", "bye"],
                            }
                        ],
                        "synonyms": [],
                        "antonyms": [],
                    },
                ],
                "sourceUrls": ["https://en.wiktionary.org/wiki/hello"],
            }
        ]

    def test_from_api_response(self, sample_api_response: list[dict]) -> None:
        """Test creating Word from API response."""
        word = Word.from_api_response(sample_api_response)

        assert word.word == "hello"
        assert len(word.phonetics) == 1
        assert len(word.meanings) == 2
        assert word.source_urls == ("https://en.wiktionary.org/wiki/hello",)

    def test_ipa_property(self, sample_api_response: list[dict]) -> None:
        """Test IPA property."""
        word = Word.from_api_response(sample_api_response)
        assert word.ipa == "/həˈloʊ/"

    def test_audio_url_property(self, sample_api_response: list[dict]) -> None:
        """Test audio URL property."""
        word = Word.from_api_response(sample_api_response)
        assert word.audio_url == "https://example.com/hello.mp3"

    def test_all_synonyms(self, sample_api_response: list[dict]) -> None:
        """Test aggregating all synonyms."""
        word = Word.from_api_response(sample_api_response)
        all_syns = word.all_synonyms
        assert "greeting" in all_syns
        assert "hi" in all_syns
        assert "hey" in all_syns

    def test_all_antonyms(self, sample_api_response: list[dict]) -> None:
        """Test aggregating all antonyms."""
        word = Word.from_api_response(sample_api_response)
        all_ants = word.all_antonyms
        assert "goodbye" in all_ants
        assert "bye" in all_ants

    def test_from_empty_response_raises(self) -> None:
        """Test that empty response raises ValueError."""
        with pytest.raises(ValueError, match="Empty API response"):
            Word.from_api_response([])


class TestBookmark:
    """Tests for Bookmark model."""

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
                                    "example": "Run the test.",
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

    def test_from_word(self, sample_word: Word) -> None:
        """Test creating Bookmark from Word."""
        bookmark = Bookmark.from_word(sample_word)

        assert bookmark.word == "test"
        assert bookmark.definition == "A procedure"
        assert bookmark.part_of_speech == "noun"
        assert bookmark.phonetic == "/test/"
        assert bookmark.example == "Run the test."
        assert "exam" in bookmark.synonyms

    def test_synonym_list(self) -> None:
        """Test synonym_list property."""
        bookmark = Bookmark(
            id=1,
            word="test",
            definition="def",
            part_of_speech="noun",
            phonetic=None,
            synonyms="one,two,three",
            antonyms="",
            example=None,
            added_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert bookmark.synonym_list == ["one", "two", "three"]

    def test_antonym_list_empty(self) -> None:
        """Test antonym_list with empty string."""
        bookmark = Bookmark(
            id=1,
            word="test",
            definition="def",
            part_of_speech="noun",
            phonetic=None,
            synonyms="",
            antonyms="",
            example=None,
            added_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert bookmark.antonym_list == []
