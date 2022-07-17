from project import get_details, print_bookmarked_words, print_bookmarks, validate_json
import pytest
import requests
import jsonschema

API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/"

# Function to test the API response


def test_get_details():
    words = ["test", "jsdsdfj", "2323"]
    for word in words:
        response = requests.get(f"{API_URL}{word}")
        if response.status_code == 200:
            json_content = response.json()
            assert get_details(word) == json_content
        elif response.status_code == 404:
            with pytest.raises(SystemExit) as e:
                get_details(word)
            assert e.type == SystemExit
            assert e.value.code == 1
        elif response.status_code >= 400 and response.status_code < 500:
            with pytest.raises(SystemExit) as e:
                get_details(word)
            assert e.type == SystemExit
            assert e.value.code == 2

        elif response.status_code >= 500 and response.status_code < 600:
            with pytest.raises(SystemExit) as e:
                get_details(word)
            assert e.type == SystemExit
            assert e.value.code == 3

# Function to test print_bookmarked_words function if path provided is wrong


def test_print_bookmarked_words_wrong_path():
    with pytest.raises(SystemExit) as e:
        print_bookmarked_words("/home/")
    assert e.type == SystemExit
    assert e.value.code == 4

# Function to test print_bookmarked_words function if bookmarks.json file is of invalid format


def test_print_bookmarked_words_invalid_json():
    with pytest.raises(SystemExit) as e:
        print_bookmarked_words("testing")
    assert e.type == SystemExit
    assert e.value.code == 5

# Function to test print_bookmarks function if given wrong path


def test_print_bookmarks_wrong_path():
    with pytest.raises(SystemExit) as e:
        print_bookmarks("/home/")
    assert e.type == SystemExit
    assert e.value.code == 4

# Function to test print_bookmarks function if bookmarks.json file is of invalid format


def test_print_bookmarks_invalid_json():
    with pytest.raises(SystemExit) as e:
        print_bookmarks("testing")
    assert e.type == SystemExit
    assert e.value.code == 5


def test_validate_json_wrong_json():
    with pytest.raises(SystemExit) as e:
        validate_json("testing/invalid1.json")
    assert e.type == SystemExit
    assert e.value.code == 8


def test_validate_json_missing_properties():
    with pytest.raises(SystemExit) as e:
        validate_json("testing/invalid2.json")
    assert e.type == SystemExit
    assert e.value.code == 8
