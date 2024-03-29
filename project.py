import argparse
import requests
import sys
import json
import time
import os.path
import playsound
import eng_to_ipa as p
from rich.progress import Progress
from rich import print
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.console import Console
from rich.table import Table
from rich.theme import Theme
from rich import box
from gtts import gTTS
from jsonschema import ValidationError, validate

# Global variables

# API URL
API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/"

# Custom theme for display messages
custom_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "danger": "bold red"
})

# Initializing console object
console = Console(theme=custom_theme)


# Function to get the response of the word


def get_details(word):

    try:
        # Progress bar hack for api request. This has nothing to do with api request.
        with Progress(transient=True) as progress:
            task = progress.add_task("[green]Fetching data...", total=10)

            while not progress.finished:
                progress.update(task, advance=0.9)
                time.sleep(0.2)

        response = requests.get(f"{API_URL}{word}", timeout=2)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            console.print(
                "Are you sure that word exists?", style="info")
            sys.exit(1)
        elif response.status_code >= 400 and response.status_code < 500:
            console.print("Client error.", style="danger")
            sys.exit(2)
        elif response.status_code >= 500 and response.status_code < 600:
            console.print(
                "A server error occured. Try again later.", style="danger")
            sys.exit(3)

    except requests.Timeout:
        console.print(
            "Error: Connection timed out. Try again later.", style="danger")
        sys.exit(5)
    except requests.ConnectionError:
        console.print(
            "Error: A connection error occured.", style="danger")
        sys.exit(6)


# Function to play the pronunciation of the word

def pronunce_word(word):
    tts = gTTS(text=word, lang='en', slow=True)
    filename = "pronunciation.mp3"
    tts.save(filename)
    # Progress bar hack for pronunciation.
    with Progress(transient=True) as progress:
        task = progress.add_task("[green]Playing pronunciation...", total=10)
        while not progress.finished:
            progress.update(task, advance=0.9)
            time.sleep(0.2)
    while True:
        playsound.playsound(filename)
        hear_again = Confirm.ask(
            "Do you want to hear again", default=True)
        if hear_again == False:
            break
    os.remove(filename)


# Function to validate json

def validate_json(json_data):
    try:
        with open("schema.json") as schema_file:
            schema = json.load(schema_file)
        validate(instance=json_data, schema=schema)
    except ValidationError:
        print("bookmarks.json not matching schema. Did you change something?")
        sys.exit(8)
    except FileNotFoundError:
        print("Could not find schema.json file. Did you remove it?")
        sys.exit(4)


# Function to print the details from response


def print_details(details):

    # Initalizing a table object
    table = Table(title="Search Results", padding=1)

    # Adding coloumns to the table
    table.add_column("Part of speech", justify="left",
                     style="#FAEA48 bold")
    table.add_column("Defintion",  justify="left", style="#66BFBF")
    table.add_column("Example", justify="center", style="#3AB4F2")

    word = details[0]["word"]
    phonetic = p.ipa_list(word)

    print(Panel(f"Word : {word.title()}, Phonetic : [italic]{phonetic}",
          title=f"Word : {word.title()}", border_style="green", style="bold"))

    # List of synonym_antonym objects
    synonym_antonym_list = []

    # Adding the partofspeech, definition and example to the table
    for i in range(len(details)):
        meanings = details[i]["meanings"]
        for meaning in meanings:
            part_of_speech = meaning["partOfSpeech"]
            # Append the synonyms and antonyms to the list
            synonym_antonym_list.append(
                {"partOfSpeech": part_of_speech, "synonyms": meaning["synonyms"], "antonyms": meaning["antonyms"]})
            definitions = meaning["definitions"]
            for definition in definitions:
                example = "__"
                if "example" in definition:
                    example = definition["example"]
                table.add_row(part_of_speech,
                              definition["definition"], example)
    # Printing the table
    console.print(table)

    # Print synonyms and antonyms
    print_synonyms_antonyms(synonym_antonym_list)

    return word

# Function to print the synonyms and antonyms of the word


def print_synonyms_antonyms(synonym_antonym_list):
    # Initializing table for synonyms and antonyms
    synonym_antonym_table = Table(
        title="Synonyms and antonyms", padding=1, box=box.ROUNDED)

    # Adding columns for part of speech, synonym and antonym
    synonym_antonym_table.add_column("Part of speech", justify="center",
                                     style="#FAEA48 bold")
    synonym_antonym_table.add_column(
        "Synonyms",  justify="center", style="#66BFBF")
    synonym_antonym_table.add_column(
        "Antonyms", justify="center", style="#3AB4F2")

    # Adding rows for each synonym antonym
    for synonym_antonym_dict in synonym_antonym_list:
        part_of_speech = synonym_antonym_dict["partOfSpeech"]
        synonyms = ", ".join(synonym_antonym_dict["synonyms"])
        antonyms = ", ".join(synonym_antonym_dict["antonyms"])
        if len(synonyms) == 0:
            synonyms = "__"
        if len(antonyms) == 0:
            antonyms = "__"
        synonym_antonym_table.add_row(
            part_of_speech, synonyms, antonyms)

    # Printing the synonym antonym table
    console.print(synonym_antonym_table)

# Function to bookmark the searched word for later review


def bookmark_word(json_details):
    # Path to the bookmarks file
    path = Prompt.ask(
        "[cyan]Enter the path where you want to bookmark the file : ", default=".")

    try:
        # Check if the bookmarks.json file exists
        if not os.path.exists(f"{os.path.join(path, 'bookmarks.json')}"):
            json_list = []
            json_list.append(json_details)
            json_object = json.dumps(json_list, indent=4)

            # Write the json object to bookmarks.json
            with open(f"{os.path.join(path, 'bookmarks.json')}", "w") as file:
                file.write(json_object)
                print(
                    f"[green]Created bookmarks.json at {path} and bookmarked word successfully.")
        # If bookmarks.json already exist
        else:
            # Read the file and deserialize it into a python object
            with open(f"{os.path.join(path, 'bookmarks.json')}", "r") as file:
                json_list = json.load(file)
                # Append the new word details into the json list
                json_list.append(json_details)
                # Serialize the json list
                json_object = json.dumps(json_list, indent=4)
            # Write the json object to a file
            with open(f"{os.path.join(path, 'bookmarks.json')}", "w") as file:
                file.write(json_object)
                print(
                    f"[green]Bookmarked word to bookmarks.json file successfully.")
    except json.JSONDecodeError:
        print("[red bold]An error occured while reading the json file.")
        sys.exit(5)

# Function to print bookmarked words


def print_bookmarked_words(path):
    # Exit if bookmarks.json does not exist
    if not os.path.exists(f"{os.path.join(path, 'bookmarks.json')}"):
        print(f"[red bold]bookmarks.json does not exist in {path}")
        sys.exit(4)
    try:
        with open(f"{os.path.join(path, 'bookmarks.json')}", "r") as file:
            word_json_list = json.load(file)
            validate_json(word_json_list)
            bookmarked_words = ""
            for word_details in word_json_list:
                bookmarked_words += "✳️" + word_details[0]["word"] + "\n"
            print(Panel(bookmarked_words, box=box.DOUBLE_EDGE,
                        title="Bookmarked Words", style="cyan"))
    except json.JSONDecodeError:
        print("[red bold]An error occured while parsing the bookmarks.json file")
        sys.exit(5)

# Function to print bookmarked words along with their details


def print_bookmarks(path):
    try:
        # Exit if bookmarks.json does not exist
        if not os.path.exists(f"{os.path.join(path, 'bookmarks.json')}"):
            print(f"[red bold]bookmarks.json does not exist in {path}")
            sys.exit(4)
        with open(f"{os.path.join(path, 'bookmarks.json')}", "r") as file:
            word_json_list = json.load(file)
            validate_json(word_json_list)
            console.rule("[bold red]Bookmarks")
            for word_details in word_json_list:
                print_details(word_details)
                console.rule(style="#6E85B7")

    except json.JSONDecodeError:
        print("[red bold]An error occured while parsing the bookmarks.json file")
        sys.exit(5)

# Function to delete bookarked word


def delete_bookmarks(delete_word,  path):
    try:
        # Exit if bookmarks.json does not exist
        if not os.path.exists(f"{os.path.join(path, 'bookmarks.json')}"):
            print(f"[red bold]bookmarks.json does not exist in {path}")
            sys.exit(4)

        word_found = False
        with open(f"{os.path.join(path, 'bookmarks.json')}", "r") as file:
            word_json_list = json.load(file)
            for index, word_details in enumerate(word_json_list):
                word = word_details[0]["word"]
                if word == delete_word:
                    print(f"Deleting {word}")
                    word_json_list.pop(index)
                    print(f"[green]Deleted word successfully")
                    word_found = True
            if not word_found:
                print("[red]That word is not bookmarked.")
        if word_found:
            with open(f"{os.path.join(path, 'bookmarks.json')}", "w") as file:
                json_object = json.dumps(word_json_list, indent=4)
                file.write(json_object)
                print(
                    f"[green]Modified bookmarks.json")

    except json.JSONDecodeError:
        print("[red bold]An error occured while parsing the bookmarks.json file")
        sys.exit(5)


# Main function


def main():
    # Intializing parser object
    parser = argparse.ArgumentParser(
        description="Commandline dictionary utility")

    group = parser.add_mutually_exclusive_group(required=True)

    # Adding an argument to view bookmarked words
    group.add_argument("-bw", help="View bookmarked words only",
                       metavar="<path to bookmarks>")

    # Adding an argument to view bookmarked words along with their meanings
    group.add_argument("-bm", help="View bookmarked words and their meanings",
                       metavar="<path to bookmarks>")

    group.add_argument("-d", nargs="+", help="Delete bookmarked word",
                       metavar="<word> <path to bookmarks>")

    # Adding word argument to parser
    group.add_argument(
        "-w", help="Get details about the given word", metavar="<word>")

    # Output of parsed arguments
    args = parser.parse_args()

    if args.d:
        try:
            delete_bookmarks(args.d[0], args.d[1])
        except IndexError:
            print(f"[bold green]Path not provided, defaulting to {(os.getcwd())}")
            delete_bookmarks(args.d[0], ".")

    # Show the bookmarked words
    if args.bw:
        print_bookmarked_words(args.bw)

    # Show the bookmarked words and their meanings
    if args.bm:
        print_bookmarks(args.bm)

    # Find details about the given word
    if args.w:
        word = args.w
        # Calling the get_details function
        details = get_details(word)

        # Printing the details
        word_returned = print_details(details)

        # Pronunce the word
        pronunce = Confirm.ask(
            "[yellow]Do you want the pronunciation of this word?", default=True)
        if pronunce:
            pronunce_word(word_returned)

        # Bookmark the word
        bookmark_current_word = Confirm.ask(
            "[yellow]Do you want to bookmark this word?", default=True)
        if bookmark_current_word:
            bookmark_word(details)


if __name__ == "__main__":
    main()
