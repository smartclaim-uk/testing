# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Playwright testing project for the SmartClaim application. The repository contains automated web tests that interact with the SmartClaim platform at various environments (staging/dev). Tests are written in Python using the Playwright framework.

## Development Setup

The project uses:
- **uv** for Python dependency management 
- **direnv** for environment management (`.envrc` automatically syncs dependencies and activates virtual environment)
- **Task** for running common commands (defined in `Taskfile.yml`)
- **Docker** for containerized testing
- **Playwright** for browser automation

### Environment Management
- Run `direnv allow` to enable automatic environment setup
- The `.envrc` file automatically runs `uv sync --no-install-project` and activates the virtual environment
- Environment variables are configured in `.env` (BASE_URL, USER_NAME)

## Common Commands

### Running Tests
- `task test` - Run tests with browser visible (headed mode)
- `task test:headless` - Run tests in background (headless mode)
- `task test:ci` - Run tests for CI environment (headless with screenshots)
- `uv run python -m pytest tests/run.py -v -s --headed --browser=chromium` - Direct pytest command

### Playwright Setup
- `uv run playwright install --with-deps` - Install Playwright browsers and dependencies
- Tests run with `headless=False` by default for development

### Docker Commands
- `task docker:build` - Build Docker image
- `task docker:run` - Run application in Docker container  
- `task docker:down` - Stop Docker containers
- Direct: `docker-compose up/down/build`

### Dependencies
- `uv sync` - Sync dependencies from pyproject.toml
- `uv add <package>` - Add new dependency

## Architecture

### Test Structure
- `/tests/run.py` - Main test file containing Playwright automation
- Test performs login flow, file upload, and status verification on SmartClaim platform
- Uses explicit waits and expects for reliable test execution

### Configuration
- `playwright.config.py` - Playwright configuration with HTML reporter
- `pyproject.toml` - Python project configuration and dependencies
- `.env` - Environment-specific configuration (BASE_URL, credentials)
- `Taskfile.yml` - Task runner configuration for common commands

### Docker Setup
- Multi-stage build using Python 3.13-slim base image
- Includes system dependencies for Playwright browsers
- Installs uv for dependency management
- Default command runs pytest test suite

## Test Data
- Test files are expected in repository root (e.g., "Martian Transcript copy.docx")
- Tests interact with staging environment by default (stg2.smartclaim.uk)

## GitHub Actions CI/CD

### Workflow Features
- **Automated Testing**: Runs on push/PR to main branch
- **HTML Report Generation**: Creates detailed test reports with screenshots
- **GitHub Pages Deployment**: Automatically serves test reports at GitHub Pages URL
- **Cross-platform**: Runs on Ubuntu with Chromium browser

### Required Secrets
Set these in GitHub repository settings → Secrets and variables → Actions:
- `BASE_URL`: Target environment URL (optional, defaults to dev2.smartclaim.uk)  
- `USER_NAME`: Test user email
- `PASSWORD`: Test user password

### Accessing Reports
After workflow runs, test reports are available at:
`https://[username].github.io/[repository-name]/`

### Manual Workflow Trigger
Workflow can be triggered manually via GitHub Actions tab → "Run Playwright Tests and Deploy Report" → "Run workflow"