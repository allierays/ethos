# Contributing to Ethos

Ethos is open source under the [MIT License](LICENSE). Contributions are welcome.

## Getting Started

1. **Fork** the repo on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ethos.git
   cd ethos
   ```
3. **Install dependencies:**
   ```bash
   # Python (engine + API)
   uv sync

   # Academy (Next.js UI)
   cd academy && npm install
   ```
4. **Set up environment:**
   ```bash
   cp .env.example .env
   # Fill in ANTHROPIC_API_KEY at minimum
   ```
5. **Start services:**
   ```bash
   # Neo4j (required for graph features)
   docker compose up neo4j -d

   # API
   uv run uvicorn api.main:app --reload --port 8000

   # Academy
   cd academy && npm run dev
   ```

## Making Changes

1. **Create a branch** from `main`:
   ```bash
   git checkout -b your-feature-name
   ```
2. **Write code** following the project conventions:
   - Python: snake_case functions, PascalCase classes, async I/O, sync computation
   - No Cypher outside `ethos/graph/`
   - No business logic in API route handlers
   - All new functionality needs tests
3. **Run tests:**
   ```bash
   uv run pytest -v
   ```
4. **Commit** with a clear message describing what changed and why

## Submitting a Pull Request

1. **Push** your branch to your fork:
   ```bash
   git push origin your-feature-name
   ```
2. **Open a pull request** against `main` on [github.com/allierays/ethos](https://github.com/allierays/ethos)
3. **Describe your changes**: what you did, why, and how to test it
4. A maintainer will review your PR. Small, focused PRs merge faster.

## What to Contribute

- Bug fixes
- Test coverage improvements
- New indicators for the taxonomy (see `ethos/taxonomy/`)
- Academy UI improvements
- Documentation

## Architecture Rules

Before contributing, read the [CLAUDE.md](CLAUDE.md) project guide. The key rules:

- **One-way dependencies**: `academy/ -> api/ -> ethos/`. Never import backwards.
- **Graph owns Cypher**: All Neo4j queries live in `ethos/graph/`.
- **Graph is optional**: Neo4j down never crashes `evaluate()`.
- **Message content is stored on Evaluation nodes**: Alongside scores and metadata.
- **All I/O is async**: Use `AsyncGraphDatabase`, `AsyncAnthropic`, async route handlers.

## Questions?

Open an [issue](https://github.com/allierays/ethos/issues) or start a [discussion](https://github.com/allierays/ethos/discussions).
