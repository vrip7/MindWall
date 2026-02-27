# Contributing to MindWall

Thank you for your interest in contributing to MindWall! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## How to Contribute

### Reporting Bugs

1. **Check existing issues** — search [GitHub Issues](https://github.com/vrip7/mindwall/issues) to avoid duplicates.
2. **Create a detailed report** using the bug report template, including:
   - OS and Docker version
   - GPU model and driver version
   - Steps to reproduce
   - Expected vs. actual behavior
   - Relevant logs (`docker compose logs -f <service>`)

### Suggesting Features

Open a [feature request](https://github.com/vrip7/mindwall/issues/new?template=feature_request.md) with:
- A clear description of the feature
- The problem it solves
- Proposed implementation approach (if any)

### Submitting Code

1. **Fork** the repository
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** following our coding standards (below)
4. **Test** your changes locally
5. **Commit** with clear, descriptive messages:
   ```
   feat(api): add rate limiting to analyze endpoint
   fix(proxy): handle malformed MIME boundaries
   docs: update API reference for /api/alerts
   ```
6. **Push** and open a Pull Request against `main`

---

## Development Setup

### Prerequisites

- Docker Desktop v24+ with Docker Compose v2
- NVIDIA GPU + drivers (for LLM inference)
- Python 3.11+ (for API/finetune development)
- Node.js 18+ (for dashboard development)

### Local Development

```bash
# Clone your fork
git clone https://github.com/<your-username>/mindwall.git
cd mindwall

# Start infrastructure (Ollama, DB)
docker compose up -d ollama

# API development
cd api
python -m venv .venv
source .venv/bin/activate    # Linux/macOS
# .\.venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Dashboard development (separate terminal)
cd dashboard
npm install
npm run dev
```

---

## Coding Standards

### Python (API, Proxy, Fine-tune)

- **Style:** Follow PEP 8, enforced by `ruff`
- **Type hints:** Required on all function signatures
- **Async:** Use `async/await` consistently — no blocking I/O in async contexts
- **Logging:** Use `structlog` — no `print()` statements
- **Config:** All settings via `pydantic-settings`, never hardcoded values
- **Docstrings:** Required for public functions and classes (Google style)

### JavaScript/React (Dashboard)

- **Style:** ESLint + Prettier (config in project)
- **Components:** Functional components with hooks only
- **State:** React hooks (`useState`, `useEffect`, `useCallback`)
- **API calls:** Centralized through `src/api/client.js`

### General

- **No mock implementations** — all code must be production-grade
- **No `TODO` or `FIXME`** comments in submitted code
- **Tests** should accompany new features
- **Documentation** should be updated for any API changes

---

## Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Code style (formatting, no logic change) |
| `refactor` | Code restructuring |
| `perf` | Performance improvement |
| `test` | Adding or updating tests |
| `build` | Build system or dependencies |
| `ci` | CI/CD configuration |
| `chore` | Maintenance tasks |

**Scopes:** `api`, `proxy`, `dashboard`, `extension`, `finetune`, `docker`, `docs`

---

## Pull Request Process

1. Ensure your branch is up to date with `main`
2. All CI checks must pass
3. At least one maintainer review is required
4. Squash commits before merging (or use squash-merge)
5. Delete the branch after merging

### PR Checklist

- [ ] Code follows project coding standards
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Documentation updated (if applicable)
- [ ] No hardcoded secrets or credentials
- [ ] Commit messages follow convention

---

## Project Architecture

Before contributing, familiarize yourself with the project structure:

- **`api/`** — FastAPI engine: analysis pipeline, REST API, WebSocket, database
- **`proxy/`** — asyncio IMAP/SMTP transparent proxy
- **`dashboard/`** — React 18 + Vite + Tailwind real-time UI
- **`extension/`** — Chrome/Firefox Manifest V3 Gmail extension
- **`finetune/`** — LLM fine-tuning pipeline (Unsloth QLoRA)

See `Docs.md` for the full architecture specification.

---

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).

---

**Questions?** Open a [discussion](https://github.com/vrip7/mindwall/discussions) or reach out to the maintainers.
