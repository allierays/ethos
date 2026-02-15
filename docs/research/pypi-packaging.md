# Publishing ethos-ai to PyPI: A Practical Guide

> **Goal:** `pip install ethos-ai` installs the package, and developers use it with:
> ```python
> from ethos_academy import evaluate, reflect
> result = evaluate("message from another agent")
> ```

This document covers everything needed to get `ethos-ai` published on PyPI using modern Python packaging standards and `uv` as the package manager.

---

## Table of Contents

1. [Package Name vs Import Name](#1-package-name-vs-import-name)
2. [Project Structure (src layout)](#2-project-structure-src-layout)
3. [pyproject.toml Configuration](#3-pyprojecttoml-configuration)
4. [API Key Management](#4-api-key-management)
5. [Dependencies Strategy](#5-dependencies-strategy)
6. [Versioning](#6-versioning)
7. [README for PyPI](#7-readme-for-pypi)
8. [Building with uv](#8-building-with-uv)
9. [Testing Before Publishing](#9-testing-before-publishing)
10. [Publishing to PyPI](#10-publishing-to-pypi)
11. [GitHub Actions CI/CD](#11-github-actions-cicd)
12. [Developer Experience Checklist](#12-developer-experience-checklist)

---

## 1. Package Name vs Import Name

PyPI does not enforce any relationship between the distribution package name (what you `pip install`) and the import package name (what you `import`). This is common -- Pillow installs as `pillow` but imports as `PIL`, for example.

For Ethos:

| Concept | Value |
|---|---|
| **PyPI distribution name** | `ethos-ai` |
| **Install command** | `pip install ethos-ai` |
| **Import name** | `ethos` |
| **Directory on disk** | `src/ethos/` |

The mapping is configured in `pyproject.toml`. The `name` field is the PyPI distribution name. The actual directory under `src/` determines the import name. Hatchling (our build backend) handles this automatically when it discovers `src/ethos/`.

**Important:** Before claiming `ethos-ai` on PyPI, verify the name is available at https://pypi.org/project/ethos-ai/. Also verify `ethos` is not already claimed as an import name by another distribution (search https://pypi.org/search/?q=ethos).

---

## 2. Project Structure (src layout)

The `src` layout is the recommended approach for packages published to PyPI. It prevents accidental imports of the development copy (Python includes the current working directory first on `sys.path`) and ensures you always test the *installed* version.

### Current Structure (flat layout)

```
ethos/
  ethos/
    __init__.py
    evaluate.py
    reflect.py
    models.py
    prompts.py
    graph.py
  api/
  tests/
  pyproject.toml
```

### Target Structure (src layout for PyPI)

```
ethos/
  src/
    ethos/
      __init__.py
      evaluate.py
      reflect.py
      models.py
      prompts.py
      graph.py
      py.typed              # marker for PEP 561 type checking support
  api/                      # FastAPI app (NOT included in the PyPI package)
  tests/
    __init__.py
    test_evaluate.py
    test_reflect.py
  scripts/
  docs/
  pyproject.toml
  README.md
  LICENSE
  .gitignore
```

**Why `src/` layout?**
- Prevents the common bug where `from ethos_academy import evaluate` silently imports the local directory instead of the installed package
- Ensures `uv run pytest` tests the installed package, not the source directory
- Only files in `src/ethos/` end up in the wheel -- no accidental inclusion of `tests/`, `scripts/`, `api/`, etc.
- This is what the [Python Packaging Authority recommends](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)

### Migration Steps

```bash
# From the ethos project root (where pyproject.toml lives)
mkdir -p src
mv ethos src/ethos

# Reinstall in editable mode to verify
uv pip install -e .

# Verify imports still work
uv run python -c "from ethos_academy import evaluate, reflect; print('OK')"
```

---

## 3. pyproject.toml Configuration

This is the single configuration file for modern Python packaging. No `setup.py`, no `setup.cfg`, no `MANIFEST.in`.

### Complete pyproject.toml for ethos-ai

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "ethos-ai"
version = "0.1.0"
description = "Evaluate AI agent messages for trustworthiness across ethos, logos, and pathos."
readme = "README.md"
license = "MIT"
requires-python = ">=3.11"
authors = [
    { name = "Ethos Contributors" },
]
keywords = ["ai", "agents", "trust", "evaluation", "safety", "alignment", "llm"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
    "Topic :: Security",
    "Typing :: Typed",
]

# Core dependencies -- keep this minimal for the SDK
dependencies = [
    "httpx>=0.27.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
# Full install for running the API server locally
server = [
    "anthropic>=0.79.0",
    "fastapi>=0.128.0",
    "neo4j>=6.1.0",
    "uvicorn>=0.40.0",
]
dev = [
    "pytest>=9.0.0",
    "ruff>=0.8.0",
]

[project.urls]
Homepage = "https://github.com/ethosai/ethos"
Documentation = "https://docs.ethos-ai.dev"
Repository = "https://github.com/ethosai/ethos"
Issues = "https://github.com/ethosai/ethos/issues"
Changelog = "https://github.com/ethosai/ethos/blob/main/CHANGELOG.md"

# Hatchling configuration for src layout
[tool.hatch.build.targets.wheel]
packages = ["src/ethos"]

# uv-specific configuration
[tool.uv]
dev-dependencies = [
    "pytest>=9.0.0",
    "ruff>=0.8.0",
    "httpx>=0.28.0",
]

# Ruff linter/formatter
[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B"]

# Pytest
[tool.pytest.ini_options]
testpaths = ["tests"]
```

### Key Decisions Explained

**`[build-system]` with Hatchling:** Hatchling is lightweight, fast, and well-supported. It handles the src layout natively. Other options (setuptools, flit, pdm-backend) all work, but Hatchling is the default for `uv init` and has the cleanest configuration.

**`[tool.hatch.build.targets.wheel] packages = ["src/ethos"]`:** This tells Hatchling to find the `ethos` package inside `src/`. Without this, it might not detect the package correctly since the distribution name (`ethos-ai`) differs from the import name (`ethos`).

**`name = "ethos-ai"` vs directory `src/ethos/`:** The `name` field is what appears on PyPI. The directory name under `src/` is what Python imports. Hatchling does not require these to match.

---

## 4. API Key Management

Ethos needs an API key to call the Ethos API. Follow the same pattern used by the Anthropic SDK, OpenAI SDK, and Stripe SDK -- the "constructor argument with environment variable fallback" pattern.

### The Pattern

```python
# src/ethos_academy/__init__.py

import os
from ethos_academy.client import EthosClient
from ethos_academy.models import EvaluationResult, ReflectionResult

__version__ = "0.1.0"

# Module-level default client (lazy initialization)
_default_client: EthosClient | None = None


def _get_client() -> EthosClient:
    global _default_client
    if _default_client is None:
        _default_client = EthosClient()
    return _default_client


def evaluate(text: str, source: str | None = None) -> EvaluationResult:
    """Evaluate text for trustworthiness."""
    return _get_client().evaluate(text, source)


def reflect(agent_id: str) -> ReflectionResult:
    """Reflect on an agent's behavior over time."""
    return _get_client().reflect(agent_id)


# Allow explicit configuration
def configure(api_key: str | None = None, base_url: str | None = None) -> None:
    """Configure the default Ethos client."""
    global _default_client
    _default_client = EthosClient(api_key=api_key, base_url=base_url)


__all__ = [
    "evaluate",
    "reflect",
    "configure",
    "EthosClient",
    "EvaluationResult",
    "ReflectionResult",
]
```

### The Client Class

```python
# src/ethos/client.py

import os
import httpx
from ethos_academy.models import EvaluationResult, ReflectionResult
from ethos_academy.exceptions import EthosAuthenticationError, EthosAPIError


ETHOS_API_KEY_ENV = "ETHOS_API_KEY"
ETHOS_BASE_URL_ENV = "ETHOS_BASE_URL"
DEFAULT_BASE_URL = "https://api.ethos-ai.dev"


class EthosClient:
    """Client for the Ethos API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or os.environ.get(ETHOS_API_KEY_ENV)
        self.base_url = base_url or os.environ.get(ETHOS_BASE_URL_ENV, DEFAULT_BASE_URL)

        if not self.api_key:
            raise EthosAuthenticationError(
                "No API key provided. Either pass api_key to EthosClient() "
                f"or set the {ETHOS_API_KEY_ENV} environment variable.\n\n"
                "  Get your API key at: https://ethos-ai.dev/api-keys"
            )

        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": f"ethos-python/{__version__}",
            },
            timeout=timeout,
        )

    def evaluate(self, text: str, source: str | None = None) -> EvaluationResult:
        """Evaluate text for trustworthiness."""
        payload = {"text": text}
        if source:
            payload["source"] = source

        response = self._client.post("/v1/evaluate", json=payload)
        response.raise_for_status()
        return EvaluationResult.model_validate(response.json())

    def reflect(self, agent_id: str) -> ReflectionResult:
        """Reflect on an agent's behavior over time."""
        response = self._client.post("/v1/reflect", json={"agent_id": agent_id})
        response.raise_for_status()
        return ReflectionResult.model_validate(response.json())

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
```

### Usage Scenarios

```python
# Scenario 1: Environment variable (recommended)
# Set ETHOS_API_KEY=sk-ethos-... in your environment or .env file
from ethos_academy import evaluate
result = evaluate("message from another agent")

# Scenario 2: Explicit API key
from ethos_academy import configure, evaluate
configure(api_key="sk-ethos-...")
result = evaluate("message from another agent")

# Scenario 3: Client instance (for multiple configs or testing)
from ethos_academy import EthosClient
client = EthosClient(api_key="sk-ethos-...", base_url="http://localhost:8917")
result = client.evaluate("message from another agent")

# Scenario 4: Context manager
from ethos_academy import EthosClient
with EthosClient(api_key="sk-ethos-...") as client:
    result = client.evaluate("message from another agent")
```

### Error Messages Matter

When the API key is missing, give a clear, actionable error:

```
ethos.exceptions.EthosAuthenticationError: No API key provided. Either pass
api_key to EthosClient() or set the ETHOS_API_KEY environment variable.

  Get your API key at: https://ethos-ai.dev/api-keys
```

This is the pattern Anthropic, OpenAI, and Stripe all use -- and it is the standard developers expect.

---

## 5. Dependencies Strategy

### Principle: Minimize for the SDK, Expand for the Server

The PyPI package (`pip install ethos-ai`) is the **SDK** -- a lightweight client that calls the Ethos API. It should have minimal dependencies. The full server (FastAPI + Neo4j + Anthropic) is a separate deployment concern.

### Core Dependencies (required for `pip install ethos-ai`)

| Package | Why | Size Impact |
|---|---|---|
| `httpx` | HTTP client for calling the Ethos API. Modern, supports async, typed. | ~500KB with httpcore, h11 |
| `pydantic` | Data validation for response models. Already ubiquitous in the Python AI ecosystem. | ~2MB |

That is it. Two dependencies.

### Why httpx Over requests

- **Async support:** `httpx` supports both sync and async, so we can add `async_evaluate()` later without a dependency change
- **Modern:** Built-in HTTP/2 support, typed, actively maintained
- **Ecosystem fit:** Anthropic SDK, OpenAI SDK, and FastAPI all use or recommend httpx
- **Comparable footprint:** Both are similar in size (~500KB)

### Why NOT Include anthropic, neo4j, fastapi

These are server-side concerns. Someone doing `pip install ethos-ai` just wants to call the API -- they should not need to install Neo4j drivers, a web framework, or the Anthropic SDK. Use optional dependency groups:

```toml
# pyproject.toml
[project.optional-dependencies]
server = ["anthropic>=0.79.0", "fastapi>=0.128.0", "neo4j>=6.1.0", "uvicorn>=0.40.0"]
```

Install with: `pip install ethos-ai[server]`

---

## 6. Versioning

### Semantic Versioning (SemVer)

Follow `MAJOR.MINOR.PATCH`:

| Bump | When | Example |
|---|---|---|
| PATCH | Bug fixes, no API changes | `0.1.0` -> `0.1.1` |
| MINOR | New features, backward compatible | `0.1.1` -> `0.2.0` |
| MAJOR | Breaking API changes | `0.2.0` -> `1.0.0` |

While in `0.x.y`, minor bumps can include breaking changes (this is pre-1.0 convention).

### Single Source of Truth

Keep the version in **one place** and reference it everywhere.

**Option A: Static in pyproject.toml (simplest)**

```toml
[project]
version = "0.1.0"
```

Then in `__init__.py`:

```python
# Read version from importlib.metadata (no duplication)
from importlib.metadata import version
__version__ = version("ethos-ai")
```

**Option B: Dynamic from __init__.py**

```toml
[project]
dynamic = ["version"]

[tool.hatch.version]
path = "src/ethos_academy/__init__.py"
```

Then in `__init__.py`:

```python
__version__ = "0.1.0"
```

Hatchling reads the version from the source file. This is useful if you want `ethos.__version__` to always be the canonical source.

### Bumping Versions with uv

```bash
# View current version
uv version

# Bump patch: 0.1.0 -> 0.1.1
uv version --bump patch

# Bump minor: 0.1.1 -> 0.2.0
uv version --bump minor

# Bump major: 0.2.0 -> 1.0.0
uv version --bump major

# Set exact version
uv version 1.0.0

# Preview without changing
uv version --bump minor --dry-run
```

---

## 7. README for PyPI

The README.md is rendered as the main content on your PyPI listing page. It is the single most important piece of marketing for your package.

### Structure for ethos-ai README

```markdown
# Ethos

[![PyPI version](https://img.shields.io/pypi/v/ethos-ai.svg)](https://pypi.org/project/ethos-ai/)
[![Python versions](https://img.shields.io/pypi/pyversions/ethos-ai.svg)](https://pypi.org/project/ethos-ai/)
[![License](https://img.shields.io/pypi/l/ethos-ai.svg)](https://github.com/ethosai/ethos/blob/main/LICENSE)

**Evaluate AI agent messages for trustworthiness.**

Ethos scores messages across three classical dimensions of persuasion: credibility (ethos),
logic (logos), and emotional appeal (pathos). Detect manipulation. Build trust graphs.
Keep humans in the loop.

## Install

\`\`\`bash
pip install ethos-ai
\`\`\`

## Quick Start

\`\`\`python
from ethos_academy import evaluate

result = evaluate("Based on peer-reviewed research, this shows a 40% improvement.")

print(result.ethos)   # 0.85 -- high credibility
print(result.logos)    # 0.90 -- strong logical basis
print(result.pathos)   # 0.20 -- low emotional manipulation
print(result.trust)    # "high"
print(result.flags)    # []
\`\`\`

## Configuration

Set your API key as an environment variable:

\`\`\`bash
export ETHOS_API_KEY="sk-ethos-..."
\`\`\`

Or pass it directly:

\`\`\`python
from ethos_academy import configure
configure(api_key="sk-ethos-...")
\`\`\`

## Documentation

Full documentation at [docs.ethos-ai.dev](https://docs.ethos-ai.dev)

## License

MIT
```

### What Makes This Effective

1. **Badges at the top** -- version, Python versions, license. Developers look for these immediately.
2. **One-sentence description** -- tells you exactly what this does.
3. **Install in one line** -- no ambiguity.
4. **Working code example** -- the entire value proposition in 6 lines of Python.
5. **Configuration section** -- answers the immediate next question: "How do I authenticate?"
6. **Short** -- PyPI listings that are too long get skimmed. Link to full docs for details.

### PyPI-Specific README Configuration

```toml
# pyproject.toml
[project]
readme = "README.md"
```

PyPI auto-detects Markdown from the `.md` extension. If you use reStructuredText, name it `README.rst`. For explicit control:

```toml
readme = { file = "README.md", content-type = "text/markdown" }
```

---

## 8. Building with uv

`uv build` creates both source distributions (`.tar.gz`) and wheel distributions (`.whl`).

### Build Commands

```bash
# Build both sdist and wheel into dist/
uv build

# Output:
#   dist/ethos_ai-0.1.0.tar.gz
#   dist/ethos_ai-0.1.0-py3-none-any.whl

# Build with sources disabled (ensures the build works without uv-specific features)
uv build --no-sources

# Build a specific package in a workspace
uv build --package ethos-ai
```

### Verify the Build

```bash
# List contents of the wheel to verify only src/ethos/ files are included
unzip -l dist/ethos_ai-0.1.0-py3-none-any.whl

# You should see:
#   ethos_academy/__init__.py
#   ethos/client.py
#   ethos_academy/models.py
#   ethos_academy/evaluate.py
#   ethos_academy/reflect.py
#   ethos/exceptions.py
#   ethos/py.typed
#   ethos_ai-0.1.0.dist-info/METADATA
#   ethos_ai-0.1.0.dist-info/WHEEL
#   ethos_ai-0.1.0.dist-info/RECORD

# NO api/, tests/, scripts/, docs/, .env, docker-compose.yml, etc.
```

### Pre-Build Checklist

Before building:
- [ ] Version bumped in pyproject.toml (or `__init__.py` if dynamic)
- [ ] CHANGELOG updated
- [ ] All tests pass: `uv run pytest -v`
- [ ] README renders correctly (preview on GitHub)
- [ ] `uv build --no-sources` succeeds (catches uv-specific config issues)
- [ ] `dist/` directory is clean: `rm -rf dist/`

---

## 9. Testing Before Publishing

### Step 1: Editable Install (Local Development)

```bash
# Install in editable mode -- changes to src/ethos/ are immediately available
uv pip install -e .

# Or with dev dependencies
uv pip install -e ".[dev]"

# Verify the import works
uv run python -c "from ethos_academy import evaluate, reflect; print('OK')"

# Run the test suite against the installed package
uv run pytest -v
```

### Step 2: Test the Built Package (Simulates pip install)

```bash
# Build the package
uv build

# Install from the built wheel in an isolated environment
uv run --with ./dist/ethos_ai-0.1.0-py3-none-any.whl --no-project -- \
    python -c "from ethos_academy import evaluate; print(evaluate.__doc__)"

# Or create a temporary venv to test
python -m venv /tmp/ethos-test
/tmp/ethos-test/bin/pip install dist/ethos_ai-0.1.0-py3-none-any.whl
/tmp/ethos-test/bin/python -c "from ethos_academy import evaluate, reflect; print('OK')"
rm -rf /tmp/ethos-test
```

### Step 3: TestPyPI (Staging)

TestPyPI is a separate instance of PyPI for testing the upload/install workflow without affecting the real index.

```bash
# 1. Register at https://test.pypi.org/account/register/

# 2. Configure TestPyPI as an index in pyproject.toml (optional)
#    Or use command-line flags

# 3. Build
uv build

# 4. Upload to TestPyPI
uv publish --publish-url https://test.pypi.org/legacy/ --token pypi-YOUR_TEST_TOKEN

# 5. Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    ethos-ai

# The --extra-index-url is needed so dependencies (httpx, pydantic) resolve from real PyPI

# 6. Verify
python -c "from ethos_academy import evaluate; print('Installed from TestPyPI!')"
```

### TestPyPI Configuration in pyproject.toml

```toml
# Add this to pyproject.toml for convenience
[[tool.uv.index]]
name = "testpypi"
url = "https://test.pypi.org/simple/"
publish-url = "https://test.pypi.org/legacy/"
```

Then publish with:

```bash
uv publish --index testpypi --token pypi-YOUR_TEST_TOKEN
```

---

## 10. Publishing to PyPI

### First-Time Setup

1. **Create a PyPI account** at https://pypi.org/account/register/
2. **Enable 2FA** (required for new projects)
3. **Create an API token** at https://pypi.org/manage/account/token/
   - Scope: "Entire account" for first upload, then create a project-scoped token after

### Publish with uv

```bash
# Ensure dist/ is clean
rm -rf dist/

# Build
uv build

# Publish to PyPI
uv publish --token pypi-YOUR_TOKEN

# Or using environment variables (better for CI)
export UV_PUBLISH_TOKEN=pypi-YOUR_TOKEN
uv publish
```

### Verify the Publication

```bash
# Install from PyPI in a fresh environment
uv run --with ethos-ai --no-project -- python -c "
from ethos_academy import evaluate, reflect
print('ethos-ai installed successfully')
"

# Use --refresh-package to bypass cache if you just published
uv run --with ethos-ai --refresh-package ethos-ai --no-project -- python -c "
import ethos
print(f'ethos-ai v{ethos.__version__}')
"
```

### After First Upload

1. **Create a project-scoped token** at https://pypi.org/manage/project/ethos-ai/settings/
2. **Set up Trusted Publishing** (see section 11) to eliminate tokens entirely

---

## 11. GitHub Actions CI/CD

### Trusted Publishing (No Tokens Needed)

PyPI supports OpenID Connect (OIDC) "trusted publishing" from GitHub Actions. No secrets to manage.

**Setup on PyPI:**
1. Go to https://pypi.org/manage/project/ethos-ai/settings/publishing/
2. Add a new publisher:
   - Owner: `ethosai`
   - Repository: `ethos`
   - Workflow: `publish.yml`
   - Environment: `pypi`

### Complete Workflow

```yaml
# .github/workflows/publish.yml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv python install ${{ matrix.python-version }}
      - run: uv sync --all-extras
      - run: uv run pytest -v

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv build
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  publish:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: pypi
      url: https://pypi.org/p/ethos-ai
    permissions:
      id-token: write  # Required for trusted publishing
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      - uses: astral-sh/setup-uv@v5
      - run: uv publish
```

### Workflow for TestPyPI (Pre-releases)

```yaml
# .github/workflows/publish-test.yml
name: Publish to TestPyPI

on:
  push:
    tags:
      - "v*.*.*rc*"  # e.g., v0.2.0rc1

jobs:
  build-and-publish:
    runs-on: ubuntu-latest
    environment:
      name: testpypi
      url: https://test.pypi.org/p/ethos-ai
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv build
      - run: uv publish --publish-url https://test.pypi.org/legacy/
```

---

## 12. Developer Experience Checklist

### The Two-Line Promise

Everything should work with:

```python
from ethos_academy import evaluate, reflect
result = evaluate("message from another agent")
```

This means:
- [ ] `pip install ethos-ai` works with no extras
- [ ] `from ethos_academy import evaluate` works immediately
- [ ] If `ETHOS_API_KEY` is not set, the error message tells you exactly what to do
- [ ] Response objects have intuitive attribute names (`result.trust`, `result.ethos`)
- [ ] No configuration files required -- environment variable is enough

### Error Messages

Every error should be:
1. **Specific** -- what went wrong
2. **Actionable** -- how to fix it
3. **Linked** -- URL to relevant docs

```python
# Bad
raise ValueError("Authentication failed")

# Good
raise EthosAuthenticationError(
    "No API key provided. Either pass api_key to EthosClient() "
    "or set the ETHOS_API_KEY environment variable.\n\n"
    "  Get your API key at: https://ethos-ai.dev/api-keys"
)
```

### Type Hints and py.typed

Include a `py.typed` marker file so that mypy and pyright recognize the package as typed:

```bash
touch src/ethos/py.typed
```

This file is empty -- its presence tells type checkers that the package supports PEP 561.

### Minimal __init__.py Exports

```python
# Only export what users need
__all__ = [
    "evaluate",
    "reflect",
    "configure",
    "EthosClient",
    "EvaluationResult",
    "ReflectionResult",
]
```

### Documentation in Docstrings

Every public function should have a docstring that reads well in `help()`:

```python
>>> import ethos
>>> help(ethos.evaluate)

evaluate(text: str, source: str | None = None) -> EvaluationResult
    Evaluate text for trustworthiness across ethos, logos, and pathos.

    Args:
        text: The text to evaluate.
        source: Optional source identifier (e.g., agent ID).

    Returns:
        EvaluationResult with scores (0-1) for ethos, logos, pathos,
        a trust level ("high", "medium", "low"), and any flags.

    Raises:
        EthosAuthenticationError: If no API key is configured.
        EthosAPIError: If the API request fails.

    Example:
        >>> from ethos_academy import evaluate
        >>> result = evaluate("Based on peer-reviewed research...")
        >>> print(result.trust)
        "high"
```

---

## Quick Reference: The Full Workflow

```bash
# 1. Restructure to src layout
mkdir -p src && mv ethos src/ethos

# 2. Update pyproject.toml (see section 3)

# 3. Install in editable mode
uv pip install -e ".[dev]"

# 4. Run tests
uv run pytest -v

# 5. Bump version
uv version --bump patch

# 6. Build
rm -rf dist/ && uv build

# 7. Verify the wheel contents
unzip -l dist/ethos_ai-*.whl

# 8. Test on TestPyPI
uv publish --publish-url https://test.pypi.org/legacy/ --token $TEST_PYPI_TOKEN
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ ethos-ai

# 9. Publish to PyPI
uv publish --token $PYPI_TOKEN

# 10. Verify
uv run --with ethos-ai --no-project -- python -c "from ethos_academy import evaluate; print('OK')"
```

---

## Sources

- [Writing your pyproject.toml - Python Packaging User Guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [pyproject.toml specification](https://packaging.python.org/en/latest/specifications/pyproject-toml/)
- [src layout vs flat layout - Python Packaging User Guide](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
- [Distribution package vs. import package - Python Packaging User Guide](https://packaging.python.org/en/latest/discussions/distribution-package-vs-import-package/)
- [Building and publishing a package - uv docs](https://docs.astral.sh/uv/guides/package/)
- [Managing Python Projects With uv - Real Python](https://realpython.com/python-uv/)
- [Using TestPyPI - Python Packaging User Guide](https://packaging.python.org/en/latest/guides/using-testpypi/)
- [Publishing with GitHub Actions - Python Packaging User Guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
- [pypi-publish GitHub Action](https://github.com/pypa/gh-action-pypi-publish)
- [Anthropic Python SDK - GitHub](https://github.com/anthropics/anthropic-sdk-python)
- [Python packages with pyproject.toml and nothing else - Simon Willison](https://til.simonwillison.net/python/pyproject)
- [README File Best Practices - pyOpenSci](https://www.pyopensci.org/python-package-guide/documentation/repository-files/readme-file-best-practices.html)
- [Python Package Structure - pyOpenSci](https://www.pyopensci.org/python-package-guide/package-structure-code/python-package-structure.html)
- [Best Practices for API Key Safety - OpenAI](https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety)
- [Python Packaging Best Practices 2026 - dasroot.net](https://dasroot.net/posts/2026/01/python-packaging-best-practices-setuptools-poetry-hatch/)
- [Make your Python package PyPI ready - pyOpenSci](https://www.pyopensci.org/python-package-guide/tutorials/pyproject-toml.html)
