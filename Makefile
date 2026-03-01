.PHONY: sync run test coverage lint format format-check typecheck pyright check ci

sync:
	uv sync --extra dev

run:
	uv run wut --help

test:
	uv run pytest tests/ -v

coverage:
	uv run pytest tests/ -v --cov=src/wut --cov-report=xml --cov-report=term-missing

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff check --fix src/ tests/
	uv run ruff format src/ tests/

format-check:
	uv run ruff format --check src/ tests/

typecheck:
	uv run mypy src/ tests/

pyright:
	uv run --with pyright pyright

check: lint typecheck test

ci: lint typecheck pyright test
