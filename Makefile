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

# --- Release Shortcuts --- #
define release
	uvx hatch version $(1)
	$(eval NEW_VERS := $(shell python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"))
	git add pyproject.toml
	git commit -m "Bump version to v$(NEW_VERS)"
	git tag v$(NEW_VERS)
	@echo "Success! Run 'git push && git push --tags' to publish the release."
endef

release-patch:
	$(call release,patch)

release-minor:
	$(call release,minor)

release-major:
	$(call release,major)
