import argparse
import requests
import sys
from rich.console import Console
from rich.table import Table
from rich.theme import Theme
import time
from rich.progress import Progress

# Function to get the response of the word


def get_details(word):
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

    try:
        # Progress bar for api request
        with Progress(transient=True) as progress:
            task = progress.add_task("[green]Fetching data...", total=10)

            while not progress.finished:
                progress.update(task, advance=0.9)
                time.sleep(0.2)

        response = requests.get(f"{API_URL}{word}", timeout=2)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            sys.exit(console.print(
                "Are you sure that word exists?", style="info"))
        elif response.status_code >= 400 and response.status_code < 500:
            sys.exit(console.print("Client error", style="danger"))
        elif response.status_code >= 500 and response.status_code < 600:
            sys.exit(console.print("A server error occured"), style="danger")

    except requests.Timeout:
        sys.exit(console.print("Error: Connection timed out."), style="danger")
    except requests.ConnectionError:
        sys.exit(console.print(
            "Error: A connection error occured."), style="danger")


# Function to print the details from response


def print_details(details):
    # Initalizing console object
    console = Console()

    # Initalizing a table object
    table = Table(title="Search Results", padding=1)

    # Adding coloumns to the table
    table.add_column("Part of speech", justify="left", style="cyan")
    table.add_column("Defintion",  justify="left", style="magenta")
    table.add_column("Example", justify="center", style="green")

    word = details[0]["word"]
    phonetic = ""
    if "phonetic" in details[0]:
        phonetic = details[0]["phonetic"]
    phonetics = details[0]["phonetics"]

    # Printing the word and phonetic
    console.print(f"{word.title()}", style="bold", end=" ")
    console.print(f"{[phonetic]}", style="italic")

    # Adding the partofspeech, definition and example to the table
    for i in range(len(details)):
        meanings = details[i]["meanings"]
        for meaning in meanings:
            part_of_speech = meaning["partOfSpeech"]
            definitions = meaning["definitions"]
            # print("Part of speech : ", part_of_speech)
            # print()
            for definition in definitions:
                # print("Definition : ", definition["definition"])
                example = "__"
                if "example" in definition:
                    # print("Example : ", definition["example"])
                    example = definition["example"]
                table.add_row(part_of_speech,
                              definition["definition"], example)
    # Printing the table
    console.print(table)

# Main function


def main():
    # Intializing parser object
    parser = argparse.ArgumentParser(
        description="Commandline dictionary utility")
    # Adding word positional argument to parser
    parser.add_argument("word", default="<word>",
                        help="Get details about the given word", metavar="word")
    # Output of parsed arguments
    args = parser.parse_args()

    # Storing the word argument into variable word
    word = args.word

    # Calling the get_details function
    details = get_details(word)

    # Printing the details
    print_details(details)


if __name__ == "__main__":
    main()
