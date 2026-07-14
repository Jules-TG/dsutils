#!/usr/bin/env python3
"""Scaffold a new Python project with a modern src layout.

Creates a parent directory named after the project, containing a
``pyproject.toml``, a ``ruff.toml``, a ``.gitignore``, a ``src/<package>``
package, a ``tests`` directory, a ``README.md``, and a ``LICENSE`` file.

By default the project is treated as private company code: it ships a
proprietary "all rights reserved" notice and a ``Private :: Do Not Upload``
classifier that makes an accidental PyPI upload fail. Pass ``--license MIT``
(or another SPDX id, or ``none``) to change that.

Examples
--------
    python new_project.py my-project
    python new_project.py my-project --company "Technopolis Group"
    python new_project.py my-project --license MIT --author "Jane Doe"
    python new_project.py my-project --path ~/code --python 3.12 --no-git
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date
from pathlib import Path

DEFAULT_COMPANY = "Technopolis Group"


def _normalise_package_name(project_name: str) -> str:
    """Turn a distribution name (my-project) into an importable name (my_project)."""
    return project_name.strip().lower().replace("-", "_").replace(" ", "_")


def _git_config(key: str) -> str | None:
    """Read a value from git config, or return None if unavailable."""
    try:
        result = subprocess.run(
            ["git", "config", "--get", key],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return None
    return result.stdout.strip() or None


def _render_pyproject(
    dist_name: str,
    package_name: str,
    description: str,
    author: str | None,
    email: str | None,
    python_version: str,
    license_id: str,
) -> str:
    """Return the contents of pyproject.toml."""
    authors = ""
    if author and email:
        authors = f'authors = [{{ name = "{author}", email = "{email}" }}]\n'
    elif author:
        authors = f'authors = [{{ name = "{author}" }}]\n'

    lic = license_id.lower()
    meta = ""
    if lic == "proprietary":
        meta += 'license = "LicenseRef-Proprietary"\n'
        meta += 'license-files = ["LICENSE"]\n'
        # Rejected by PyPI, so an accidental `twine upload` fails safely.
        meta += 'classifiers = ["Private :: Do Not Upload"]\n'
    elif lic != "none":
        meta += f'license = "{license_id}"\n'
        meta += 'license-files = ["LICENSE"]\n'

    return f'''[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{dist_name}"
version = "0.1.0"
description = "{description}"
readme = "README.md"
requires-python = ">={python_version}"
{meta}{authors}dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "ruff>=0.6",
    "mypy>=1.10",
]

[tool.hatch.build.targets.wheel]
packages = ["src/{package_name}"]

# Ruff is configured in the project's ruff.toml.

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra"

[tool.mypy]
python_version = "{python_version}"
strict = true
files = ["src", "tests"]
'''


def _render_gitignore() -> str:
    """Return a standard Python .gitignore."""
    return """# Operating System Files
.DS_Store
.AppleDouble
.LSOverride
._*
.DocumentRevisions-V100
.fseventsd
.Spotlight-V100
.Trashes
.VolumeIcon.icns
.com.apple.timemachine.donotpresent

# Python Virtual Environments
.venv/
venv/
ENV/
env/

# Python Bytecode and Cache
__pycache__/
*.py[cod]
*$py.class

# Distribution / Packaging
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Environment Variables / Secrets
.env
.env.local
.env.*.local
*.env

# Testing and Coverage
.cache
.pytest_cache/
.tox/
.coverage
.coverage.*
.htmlcov/
nosetests.xml
coverage.xml
*.cover
.hypothesis/

# IDEs and Editors
.vscode/
.idea/
*.swp
*.swo

# Output files
*.csv
*.xlsx
*.xls
*.json
*.parquet
*.zip
*.gz
*.tsv
*.feather
*.h5
*.hdf5
*.pkl
*.pickle
*.npy
*.npz
*.db
*.sqlite
*.sqlite3

"""


def _render_ruff_toml(python_version: str) -> str:
    """Return a standalone ruff.toml pinned to the project's Python version."""
    target = "py" + python_version.replace(".", "")
    return f'''line-length = 88
target-version = "{target}"

[lint]
# Enable specific rule sets (e.g., Pyflakes, Rule/Error, Isort, Naming)
select = ["E", "F", "I", "N"]
unfixable = ["F401"]

[lint.pydocstyle]
convention = "google"

[format]
quote-style = "double"
indent-style = "space"
preview = true
'''


def _render_readme(dist_name: str, package_name: str, description: str) -> str:
    """Return the README.md contents."""
    return f"""# {dist_name}

{description or "A new Python project."}

## Installation

```bash
pip install -e ".[dev]"
```

## Usage

```python
import {package_name}
```

## Development

```bash
pytest
ruff check .
mypy
```
"""


def _render_test(package_name: str) -> str:
    """Return a minimal test module."""
    return f"""from {package_name} import __version__


def test_version() -> None:
    assert isinstance(__version__, str)
"""


def _render_proprietary_license(year: int, company: str) -> str:
    """Return a short 'all rights reserved' proprietary notice."""
    return f"""Copyright (c) {year} {company}. All rights reserved.

This software and its source code are the confidential and proprietary
property of {company}. Unauthorised copying, distribution, modification, or
use of this software, in whole or in part, by any means, is strictly
prohibited without the prior written permission of {company}.
"""


def _render_mit_license(year: int, holder: str) -> str:
    """Return the text of the MIT licence."""
    return f"""MIT License

Copyright (c) {year} {holder}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def _write(path: Path, content: str) -> None:
    """Write a file and report the path relative to the current directory."""
    path.write_text(content, encoding="utf-8")
    try:
        shown = path.relative_to(Path.cwd())
    except ValueError:
        shown = path
    print(f"  created {shown}")


def _init_git(root: Path) -> None:
    """Run git init in the project root, tolerating a missing git."""
    try:
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        print("  initialised empty git repository")
    except FileNotFoundError:
        print("  note: git not found, skipping git init")
    except subprocess.CalledProcessError:
        print("  note: git init failed, skipping")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scaffold a new Python project with a src layout.",
    )
    parser.add_argument("name", help="Project (distribution) name, e.g. my-project")
    parser.add_argument(
        "--path",
        default=".",
        help="Directory in which to create the project (default: current dir)",
    )
    parser.add_argument("--description", default="", help="Short project description")
    parser.add_argument(
        "--author",
        default=None,
        help="Author name (defaults to git config user.name)",
    )
    parser.add_argument(
        "--email",
        default=None,
        help="Author email (defaults to git config user.email)",
    )
    parser.add_argument(
        "--company",
        default=DEFAULT_COMPANY,
        help=f"Copyright holder for the licence (default: {DEFAULT_COMPANY})",
    )
    parser.add_argument(
        "--python",
        default="3.11",
        help="Minimum Python version (default: 3.11)",
    )
    parser.add_argument(
        "--license",
        default="proprietary",
        help='Licence: "proprietary" (default), "none", "MIT", or any SPDX id',
    )
    parser.add_argument(
        "--no-git",
        action="store_true",
        help="Do not run git init",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Proceed even if the target directory already exists",
    )
    return parser.parse_args(argv)


def create_project(argv: list[str] | None = None) -> int:
    """Scaffold a new Python project with a modern src layout.

    Creates a new project directory containing `pyproject.toml`,
    `.gitignore`, `ruff.toml`, a `src/<package>` package, a `tests`
    directory, `README.md`, and a `LICENSE` file. Optionally initialises
    a git repository.

    Args:
        argv: Command-line arguments to parse. When `None`, the arguments
            are read from `sys.argv`.

    Returns:
        An exit code: 0 on success, 1 if the project name is invalid or
        the target directory already exists.
    """
    args = _parse_args(argv)

    dist_name = args.name.strip()
    package_name = _normalise_package_name(dist_name)

    if not package_name.isidentifier():
        print(
            f"error: '{dist_name}' does not map to a valid package name "
            f"(got '{package_name}')",
            file=sys.stderr,
        )
        return 1

    root = (Path(args.path).expanduser().resolve()) / dist_name
    if root.exists() and any(root.iterdir()) and not args.force:
        print(
            f"error: {root} already exists and is not empty (use --force to override)",
            file=sys.stderr,
        )
        return 1

    author = args.author or _git_config("user.name")
    email = args.email or _git_config("user.email")
    company = args.company
    lic = args.license.lower()
    year = date.today().year

    src_pkg = root / "src" / package_name
    tests_dir = root / "tests"
    src_pkg.mkdir(parents=True, exist_ok=True)
    tests_dir.mkdir(parents=True, exist_ok=True)

    print(f"Scaffolding '{dist_name}' at {root}")

    _write(
        root / "pyproject.toml",
        _render_pyproject(
            dist_name,
            package_name,
            args.description,
            author,
            email,
            args.python,
            args.license,
        ),
    )
    _write(root / ".gitignore", _render_gitignore())
    _write(root / "ruff.toml", _render_ruff_toml(args.python))
    _write(
        root / "README.md", _render_readme(dist_name, package_name, args.description)
    )
    _write(src_pkg / "__init__.py", '__version__ = "0.1.0"\n')
    _write(tests_dir / "__init__.py", "")
    _write(tests_dir / f"test_{package_name}.py", _render_test(package_name))

    if lic == "proprietary":
        _write(root / "LICENSE", _render_proprietary_license(year, company))
    elif lic == "mit":
        _write(root / "LICENSE", _render_mit_license(year, author or company))
    elif lic != "none":
        print(
            f"  note: pyproject.toml references '{args.license}' but no LICENSE file "
            "was generated. Add your own."
        )

    if not args.no_git:
        _init_git(root)

    _write(root / ".env", "")
    _write(root / ".env.example", "")

    print("\nDone. Next steps:")
    print(f"  cd {dist_name}")
    print("  uv venv --python 3.14.4 .venv && source .venv/bin/activate")
    print('  uv pip install -e ".[dev]"')
    return 0


if __name__ == "__main__":
    raise SystemExit(create_project())
