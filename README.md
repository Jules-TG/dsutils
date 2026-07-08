# Jules Stremersch's library of assorted reusable Python code for working with data

## Installation

Requires Python >= 3.14.

This library contains a large variety of functions, so most dependencies are
optional. Install only those you need. The following uses the api module as an
example:

### As a dependency (recommended)

Add to your `pyproject.toml`:

```toml
[project]
dependencies = ["dsutils[api] @ git+https://github.com/Jules-TG/dsutils@v0.1.0"]
```

Or with `uv`:

```
uv add "dsutils[api] @ git+https://github.com/Jules-TG/dsutils@v0.1.0"
```

### Ad-hoc install

```
uv pip install "dsutils[api] @ git+https://github.com/Jules-TG/dsutils@v0.1.1"
```

## Documentation

To run the documentation locally:

```
source .venv/bin/activate
uv pip install -e ".[dev]"
uv run zensical serve
```
