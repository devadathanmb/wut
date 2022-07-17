from project import get_details, print_bookmarked_words, print_bookmarks
import pytest
import requests
import json

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
        print_bookmarked_words("/home/bookmarks.json")
    assert e.type == SystemExit
    assert e.value.code == 4

# Function to test print_bookmarked_words function if bookmarks.json file is of invalid format


def test_print_bookmarked_words_invalid_json():
    with pytest.raises(SystemExit) as e:
        print_bookmarked_words("test")
    assert e.type == SystemExit
    assert e.value.code == 5

# Function to test print_bookmarks function if given wrong path


def test_print_bookmarks_wrong_path():
    with pytest.raises(SystemExit) as e:
        print_bookmarks("/home/bookmarks.json")
    assert e.type == SystemExit
    assert e.value.code == 4

# Function to test print_bookmarks function if bookmarks.json file is of invalid format


def test_print_bookmarks_invalid_json():
    with pytest.raises(SystemExit) as e:
        print_bookmarks("test")
    assert e.type == SystemExit
    assert e.value.code == 5
