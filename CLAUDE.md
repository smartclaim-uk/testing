# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Playwright testing project for the SmartClaim application. Tests are written in Python using pytest + Playwright, targeting staging/dev environments. Tests perform login, file upload, content generation, and cleanup flows.

## Development Setup

- **uv** for dependency management
- **direnv** for environment (`.envrc` runs `uv sync` and activates `.venv`)
- **Task** (go-task) for common commands
- Run `direnv allow` after cloning

### Environment Variables (`.env`)
- `BASE_URL` - Target environment URL
- `USER_NAME` - Test user email
- `PASSWORD` - Test user password

## Commands

### Tests
- `task test` - Run tests headed (browser visible)
- `task test:headless` - Run tests headless
- `task test:ci` - Run tests for CI (headless + screenshots)
- Single test: `uv run python -m pytest tests/run.py::test_draft -v -s --headed --browser=chromium`

### Formatting
- `uv run black .` - Format code
- `uv run isort .` - Sort imports
- `uv run autoflake --remove-all-unused-imports -r .` - Remove unused imports

### Docker
- `task docker:build` / `task docker:run` / `task docker:down`

### Playwright
- `uv run playwright install --with-deps` - Install browsers

## Architecture

### Test Flow (`tests/run.py`)
All tests use `per_component(page, module, submodules)` which executes:
1. **Login** - Navigate to BASE_URL, authenticate with credentials
2. **Upload** - Upload `output.pdf` to the selected module
3. **Wait for processing** - Poll `#status-text-{file_id}` until "Ready" (3 min timeout)
4. **Accept & Submit** - Click Accept/Submit buttons
5. **Verify submodules** - Assert each submodule's `#main-content-{module}_{submod}_{subsubmod}` has content (5 min timeout per submodule)
6. **Cleanup** - Delete uploaded file via `#delete-button-{file_id}`

File ID is extracted from `window.localStorage.getItem('global_state')`.

### Test Functions
- `test_draft` - Tests draft module with 5 questions
- `test_review` - Tests review module (overall, eligibility, baseline, advance, uncertainty, resolution)
- `test_qualify` - Tests qualify module (overall_assessment, baseline_research, risk_factors, narrative_content_coverage)
- `test_defend` - Stub (empty)

### Fixtures (`conftest.py`)
- `browser` (session-scoped) - Launches Chromium headless
- `page` (function-scoped) - Creates context with video recording (1280x720), yields page, closes context

### Default pytest options (`pytest.ini`)
`--html=report.html --self-contained-html --screenshot=on --video=on --tracing=on -s --log-level=INFO --output=test-results`

## CI/CD

GitHub Actions workflow runs on push/PR to main and daily at midnight UTC. Deploys HTML test reports to GitHub Pages.

### Required Secrets
- `USER_NAME`, `PASSWORD` - Test credentials
- `BASE_URL` - Target URL (optional, defaults to dev2.smartclaim.uk)
- `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID` - Optional notification on success
