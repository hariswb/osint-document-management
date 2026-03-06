# OSINT CLI

An OSINT (Open Source Intelligence) Named Entity Recognition tool built with Python, Typer, DuckDB, and Transformers.

## Features

- Named Entity Recognition using pre-trained transformer models
- DuckDB for efficient data storage and querying
- Document processing support (PDF, text)
- KSEI Balance Position data integration
- Rich CLI interface

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd osint-cli

# Install dependencies with UV
uv sync
```

## Usage

```bash
# Initialize database
uv run python -m src.main init

# Show version
uv run python -m src.main version
```

## Development

This is Day 1 of a 7-day MVP sprint.

## License

MIT
