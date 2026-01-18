.PHONY: install test build clean release help

VERSION := $(shell grep "^version =" pyproject.toml | sed 's/version = "\(.*\)"/\1/')


help:
	@echo "Available targets:"
	@echo "  install  - Install dependencies using uv"
	@echo "  test     - Run tests using uv run pytest"
	@echo "  build    - Build the package using uv build"
	@echo "  release  - Tag and push a new release based on the version in pyproject.toml"
	@echo "  clean    - Remove build artifacts and pycache"

install:
	uv sync

test:
	uv run pytest $(ARGS)

build:
	uv build

release:
	@echo "Releasing version $(VERSION)..."
	git tag -a $(VERSION) -m "Tag $(VERSION)"
	git push origin main
	git push origin $(VERSION)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".pytest_cache" -exec rm -rf {} +
	rm -rf dist build *.egg-info .venv
