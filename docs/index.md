# dsutils

Jules Stremersch's library of assorted reusable Python code for working with data

A collection of self-contained Python utility functions for common tasks:

- **io** - JSON file read/write utilities
- **api** - HTTP request wrapper with retry logic
- **data** - List comparison and collection utilities
- **llm** - Azure OpenAI sync and async clients

## Quick start

```bash
uv pip install -e .
```

## Usage

```python
from dsutils.io.json import load_json, save_json
from dsutils.api.client import send_request
from dsutils.data.collections import compare_lists
```
