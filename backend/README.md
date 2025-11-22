# Backend

This directory contains the Python backend for the YouTube Analyzer application.

## Setup

This project is managed with `uv`.

1.  Install `uv` if you haven't already:
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2.  Sync dependencies:
    ```bash
    uv sync
    ```

## Running

To run the downloader script:
```bash
uv run python main.py <youtube_url>
```

## Testing

To run the tests:
```bash
PYTHONPATH=. uv run pytest tests/
```
