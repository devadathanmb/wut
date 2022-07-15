import argparse


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


if __name__ == "__main__":
    main()
