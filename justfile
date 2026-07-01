default:
    @just --list

sync:
    uv sync --all-packages
    uv run prek install

dev:
    uv run lst-bot

format:
    uv run --all-packages ruff format

lint: format
    uv run --all-packages ruff check --fix

tc: lint
    uv run --all-packages ty check

test: tc
    uv run --all-packages pytest

check:
    uv lock --check
    uv run --all-packages ruff format --check
    uv run --all-packages ruff check
    uv run --all-packages ty check

build: check
    uv build --all-packages --no-create-gitignore --no-sources

clean:
    fd -I -t d -F __pycache__ -x rm -rf
    rm -rf dist/ .pytest_cache/ .ruff_cache/
    uv run --all-packages ruff clean
