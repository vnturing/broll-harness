.PHONY: install dev run lint format clean

# Install production dependencies
install:
	uv sync --no-dev

# Install all dependencies (including dev)
dev:
	uv sync

# Run the dev server
run:
	uv run uvicorn app.main:app --reload --port 8000

# Run tests
test:
	uv run pytest

# Format code
format:
	uv run ruff format app/

# Lint code
lint:
	uv run ruff check app/

# Remove virtual environment and cached files
clean:
	rm -rf .venv __pycache__ .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
