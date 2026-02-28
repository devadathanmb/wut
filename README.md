# Wut? 🤔

A modern CLI dictionary with pronunciation and bookmarking.

https://user-images.githubusercontent.com/84301852/201028904-8580cad9-ffe6-4d43-922c-aa0d780309f2.mp4

## Features

- 📖 **Word Lookup** - Get definitions, synonyms, antonyms, and examples
- 🔊 **Pronunciation** - Hear words pronounced using text-to-speech
- 🔖 **Bookmarks** - Save words for later review
- 🎨 **Rich Output** - Beautiful terminal formatting with colors and tables

## Installation

### From PyPI (coming soon)

```bash
pip install wut-cli
```

### From Source

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/devadathanmb/wut.git
cd wut
uv sync
```

## Usage

### Quick Lookup

```bash
# Look up a word (simplest form)
wut hello

# Look up and play pronunciation
wut hello -p

# Look up and bookmark
wut hello -b

# Interactive mode (prompts for pronunciation/bookmark)
wut hello -i

# Explicit lookup command also works
wut lookup hello -p -b
```

### Bookmarks

```bash
# Add a word to bookmarks
wut bookmark add hello

# List all bookmarks
wut bookmark list

# Search bookmarks
wut bookmark list -s hel

# Show bookmark details
wut bookmark show hello

# Delete a bookmark
wut bookmark delete hello

# Clear all bookmarks
wut bookmark clear
```

### Pronunciation

```bash
# Play pronunciation of a word
wut pronounce hello

# Slow pronunciation
wut pronounce hello -s
```

### Info

```bash
# Show database location and stats
wut info
```

## How It Works

Wut uses the [Free Dictionary API](https://dictionaryapi.dev/) to fetch word definitions and metadata. Bookmarks are stored in a local SQLite database in your system's application data directory.

### Tech Stack

- **CLI Framework**: [Click](https://click.palletsprojects.com/)
- **HTTP Client**: [httpx](https://www.python-httpx.org/)
- **Terminal UI**: [Rich](https://rich.readthedocs.io/)
- **Text-to-Speech**: [gTTS](https://gtts.readthedocs.io/)
- **Database**: SQLite with [platformdirs](https://platformdirs.readthedocs.io/) for cross-platform paths

## Known Issues

Since the application uses the [Free Dictionary API](https://dictionaryapi.dev/), the output is completely dependent on the API response. The API may be missing some words or experience downtime during heavy traffic.

## Development

```bash
# Install dev dependencies
uv sync --extra dev

# Run tests
uv run pytest tests/ -v

# Run type checks
uv run mypy src/ tests/
uv run --with pyright pyright

# Run lint
uv run ruff check src/ tests/

# Run the CLI
uv run wut --help
```

## License

MIT
