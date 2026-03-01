# Wut? 🤔

Wut? _(What?)_ is a command-line dictionary for quick lookups, pronunciation, and personal word bookmarks.

Originally built as my [CS50P](https://pll.harvard.edu/course/cs50s-introduction-programming-python) final project, now completely rewritten from scratch.

> The name came from those moments while reading where you hit a word and think, "wut?"

https://github.com/user-attachments/assets/cd46c9b0-7d82-4541-9123-69d05b2b16e7

## Table of Contents

- [Wut? 🤔](#wut-)
- [Why This Exists](#why-this-exists)
- [What It Does](#what-it-does)
- [Installation](#installation)
  - [From PyPI (Recommended)](#from-pypi-recommended)
  - [From Source](#from-source)
- [Usage](#usage)
  - [Quick Lookup](#quick-lookup)
  - [Bookmarks](#bookmarks)
  - [Pronunciation](#pronunciation)
  - [Info](#info)
- [Development](#development)
- [Credits](#credits)
- [License](#license)
- [Known Limitations](#known-limitations)

## Why This Exists

While reading articles, documentation, or even chats, you often run into words you half-know or do not know at all.

Most of the time, the flow is the same: switch tabs, open a search engine or dictionary, type the word, then come back. Wut? exists to reduce that context switching. You stay in the terminal, get the meaning fast, hear pronunciation when needed, and bookmark words you want to revisit later.

## What It Does

- Looks up definitions, examples, synonyms, and antonyms
- Plays pronunciation for words
- Saves and manages bookmarks locally

## Installation

### From PyPI (Recommended)

```bash
pipx install wut-dictionary-cli
```

Then run:

```bash
wut --help
```

If `pipx` is not installed:

```bash
python -m pip install --user pipx
python -m pipx ensurepath
```

### From Source

```bash
git clone https://github.com/devadathanmb/wut.git
cd wut
pipx install . --force
```

## Usage

### Quick Lookup

```bash
# Simplest form
wut hello

# Lookup + pronunciation
wut hello -p

# Lookup + bookmark
wut hello -b

# Interactive prompts
wut hello -i

# Explicit lookup command
wut lookup hello -p -b
```

### Bookmarks

```bash
# Add
wut bookmark add hello

# List
wut bookmark list

# List with search
wut bookmark list -s hel

# Show one
wut bookmark show hello

# Delete one
wut bookmark delete hello

# Clear all
wut bookmark clear
```

### Pronunciation

```bash
# Normal speed
wut pronounce hello

# Slow speed
wut pronounce hello -s
```

### Info

```bash
# Database path + bookmark count
wut info
```

## Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency and environment management.

1. Install prerequisites.

```bash
python --version
uv --version
```

2. Clone the repository.

```bash
git clone https://github.com/devadathanmb/wut.git
cd wut
```

3. Create the local dev environment and install dependencies.

```bash
uv sync --extra dev
```

4. Run the CLI locally.

```bash
uv run wut --help
uv run wut hello
```

5. Run tests.

```bash
make test
```

6. Run lint and type checks.

```bash
make lint
make typecheck
make pyright
```

7. Run all default quality checks together.

```bash
make check
make coverage
```

8. Optional: activate `.venv` if you prefer direct commands.

```bash
source .venv/bin/activate
pytest tests/ -v
ruff check src/ tests/
```

## Credits

- [Free Dictionary API](https://dictionaryapi.dev/) for the dictionary data used by this project.

## License

[GNU Affero General Public License v3.0 (AGPL-3.0)](./LICENSE)

## Known Limitations

Dictionary results depend on the Free Dictionary API. If a word is missing there, or the service is temporarily down, Wut? will fail to fetch results.
