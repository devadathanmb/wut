# Wut?

Wut? is a command-line dictionary for quick word lookups, pronunciation, and bookmarks.

> The name came from those moments while reading where you hit a word and think: "wut?"

## What It Does

- Look up definitions, examples, synonyms, and antonyms
- Play pronunciation for a word
- Save and manage bookmarks locally

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
- Python 3.11+
- `uv`

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
uv run pytest tests/ -v
```

6. Run lint checks.

```bash
uv run ruff check src/ tests/
```

7. Run type checks.

```bash
uv run mypy src/ tests/
uv run --with pyright pyright
```

8. Optional: activate `.venv` if you prefer direct commands.

```bash
source .venv/bin/activate
pytest tests/ -v
ruff check src/ tests/
```

## Credits

- [Free Dictionary API](https://dictionaryapi.dev/) for the dictionary data used by this project.

## Known Limitations

Dictionary results depend on the Free Dictionary API. If a word is missing there, or the service is temporarily down, Wut? will fail to fetch results.

## License

GNU Affero General Public License v3.0 (AGPL-3.0)