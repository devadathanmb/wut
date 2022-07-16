import argparse
import requests
import json
import sys

# Function to get the response of the word


def get_details(word):
    API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/"
    try:
        response = requests.get(f"{API_URL}{word}", timeout=2)
        if response.status_code == 200:
            print("Word Exists")
            details = response.json()
        elif response.status_code == 404:
            sys.exit("Are you sure that word exists?")
        elif response.status_code >= 400 and response.status_code < 500:
            sys.exit("Client error")
        elif response.status_code >= 500 and response.status_code < 600:
            sys.exit("A server error occured")

    except requests.Timeout:
        sys.exit("Error: Connection timed out.")
    except requests.ConnectionError:
        sys.exit("Error: A connection error occured.")

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
    get_details(word)


if __name__ == "__main__":
    main()
