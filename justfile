# Beanstalk task runner. `just check` runs everything CI runs.

default: check

# Install/sync all dependencies
install:
    uv sync

# Auto-format and auto-fix lint issues
fmt:
    uv run ruff format .
    uv run ruff check --fix .

# Lint + format check (no changes)
lint:
    uv run ruff format --check .
    uv run ruff check .

# Type-check with pyright (the gate)
typecheck:
    uv run pyright

# Type-check with ty — informational only, never fails the build
typecheck-ty:
    -uv run ty check src tests

# Enforce the architecture contracts (import-linter)
imports:
    uv run lint-imports

# Run only the custom architecture checks
arch:
    uv run pytest tests/arch

# Full test suite (includes arch checks)
test:
    uv run pytest

# Dependency hygiene
deps:
    uv run deptry src

# Train the risk model and write the artifact
train:
    uv run python -m beanstalk.model.train

# Run the partner-facing API on :8000
api:
    uv run uvicorn --factory beanstalk.api.app:create_app --reload --port 8000

# Run the reviewer UI on :8001
ui:
    uv run uvicorn --factory beanstalk.ui.app:create_app --reload --port 8001

# Everything CI runs, in order of fail-fast usefulness
check: lint typecheck typecheck-ty imports test deps
