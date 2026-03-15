.PHONY: sync run test coverage lint format format-check typecheck pyright check ci release

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

release:
	@test -n "$(BUMP)" || (echo "Usage: make release BUMP=patch|minor|major" && exit 1)
	uv version --bump $(BUMP)
	git add pyproject.toml uv.lock
	git commit -m "chore(release): bump version to $$(uv version --short)"
	git tag -a "v$$(uv version --short)" -m "Release v$$(uv version --short)"
	git push --follow-tags
