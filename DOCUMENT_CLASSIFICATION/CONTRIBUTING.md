# Contributing to SmartDoc AI

Thanks for taking the time to contribute. This document covers the workflow, code standards, and review process.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Branch Strategy](#branch-strategy)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Security Disclosures](#security-disclosures)

---

## Getting Started

1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```bash
   git clone https://github.com/<your-username>/ai_file_organiser.git
   cd ai_file_organiser
   ```
3. Add the upstream remote:
   ```bash
   git remote add upstream https://github.com/amisha-bitflow/ai_file_organiser.git
   ```
4. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
5. Copy `.env.example` to `.env` and fill in values.

---

## Branch Strategy

| Branch | Purpose |
|---|---|
| `main` | Stable, production-ready code |
| `develop` | Integration branch for completed features |
| `feature/<name>` | New features or enhancements |
| `fix/<name>` | Bug fixes |
| `chore/<name>` | Tooling, CI, dependency updates |

Create branches off `develop`, not `main`.

---

## Development Workflow

```bash
# Sync with upstream before starting
git fetch upstream
git checkout develop
git merge upstream/develop

# Create your branch
git checkout -b feature/my-feature

# ... make changes ...

# Run checks before committing
black app/ tests/
flake8 app/ tests/
pytest --cov=app tests/

# Commit and push
git push origin feature/my-feature
```

---

## Code Standards

- **Formatter:** [Black](https://github.com/psf/black) with default settings (line length 88)
- **Linter:** Flake8 — fix all warnings before opening a PR
- **Import order:** isort compatible with Black (`isort --profile black`)
- **Type hints:** Add them to new public functions and class methods
- **Docstrings:** NumPy-style for modules and classes; short one-liners for simple helpers

Run all checks at once:

```bash
black app/ tests/
isort --profile black app/ tests/
flake8 app/ tests/
```

---

## Testing Requirements

- Write tests for any new behaviour in `tests/`.
- Aim to keep overall coverage above 80%.
- Tests must pass locally before opening a PR — the CI pipeline will also run them.

```bash
# Full suite with coverage
pytest --cov=app --cov-report=term-missing tests/

# A single test file
pytest tests/test_classifier.py -v
```

---

## Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <short description>

[optional body]

[optional footer]
```

**Types:** `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `perf`, `ci`

Examples:
```
feat(classifier): add spaCy NER as a pre-processing step
fix(upload): reject files exceeding MAX_CONTENT_LENGTH before reading
docs(readme): update Docker setup instructions
test(auth): add coverage for token refresh endpoint
```

---

## Pull Request Process

1. Ensure your branch is up to date with `develop`.
2. Fill in the PR template (title, description, linked issue, testing steps).
3. All CI checks must pass.
4. At least one review approval is required before merging.
5. Squash commits when merging to keep the history clean.

---

## Reporting Bugs

Open a [GitHub Issue](https://github.com/amisha-bitflow/ai_file_organiser/issues/new) and include:

- A clear, descriptive title
- Steps to reproduce
- Expected vs. actual behaviour
- Python version, OS, and any relevant logs

---

## Security Disclosures

**Do not open a public GitHub issue for security vulnerabilities.**

Please report them privately via the [GitHub Security Advisory](https://github.com/amisha-bitflow/ai_file_organiser/security/advisories/new) page. See [SECURITY.md](SECURITY.md) for the full disclosure policy.
