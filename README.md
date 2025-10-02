# SmartClaim Testing Suite

## Project Overview
This repository contains automated Playwright tests for the SmartClaim application. The tests validate the document upload and processing workflow on the SmartClaim platform.

## CI/CD Workflow

### Overview
The GitHub Actions workflow (`test-and-deploy.yml`) automatically runs tests on every push/PR to the main branch and deploys detailed test reports to GitHub Pages.

### Workflow Triggers
- **Push**: Automatically runs on pushes to `main` or `master` branches
- **Pull Request**: Runs on PRs targeting `main` or `master` branches  
- **Manual**: Can be triggered manually via GitHub Actions UI (`workflow_dispatch`)

### Test Execution Process

1. **Environment Setup**
   - Uses Ubuntu latest runner
   - Installs Python 3.13 and uv package manager
   - Syncs project dependencies via `uv sync`
   - Installs Chromium browser with Playwright

2. **Test Configuration**
   - Creates test documents dynamically (simple text files for fast processing)
   - Uses environment variables from GitHub Secrets:
     - `BASE_URL`: Target environment (defaults to `https://dev2.smartclaim.uk`)
     - `USER_NAME`: Test user email
     - `PASSWORD`: Test user password

3. **Test Execution**
   - Runs pytest with Playwright in Chromium browser
   - Captures screenshots (`--screenshot=on`) 
   - Records videos (`--video=on`)
   - Generates self-contained HTML report (`--html=report.html --self-contained-html`)
   - Continues workflow even if tests fail (`continue-on-error: true`)

### Reporting System

#### Report Generation
1. **HTML Report Enhancement**
   - `fix-html-media.py` script post-processes the pytest HTML report
   - Fixes broken media links for screenshots and videos
   - Adds a media gallery section with all captured screenshots and videos
   - Maps test steps to their corresponding media files

2. **Index Page Creation**
   - `create-index.py` generates a dashboard for GitHub Pages
   - Displays latest test run information (timestamp, status, commit, branch)
   - Maintains test history (last 20 runs) in `report-history.json`
   - Provides quick links to:
     - Main test report
     - Screenshot gallery
     - Video recordings
     - Playwright report (if available)

#### GitHub Pages Deployment
1. **Artifact Preparation**
   - Copies all test artifacts to `_site/` directory:
     - `report.html`: Main pytest report
     - `screenshots/`: Test screenshots
     - `test-results/`: Video recordings (.webm files)
     - `playwright-report/`: Additional Playwright reports
   
2. **History Preservation**
   - Downloads previous GitHub Pages artifact (if exists)
   - Extracts and preserves `report-history.json`
   - Merges with new test results

3. **Deployment**
   - Uploads `_site/` as GitHub Pages artifact
   - Deploys to GitHub Pages environment
   - Report accessible at: `https://[username].github.io/[repository-name]/`

### Report Features

#### Media Gallery
- Automatically embeds screenshots and videos in the HTML report
- Creates a visual gallery section with:
  - Thumbnails of all screenshots with filenames
  - Video players for test recordings
  - Organized by test steps and test functions

#### Test History Tracking
- Maintains JSON history of last 20 test runs
- Tracks for each run:
  - Timestamp and date/time
  - Test status (Passed/Failed/Unknown)
  - Git commit SHA (first 8 characters)
  - Branch name
- Displays history in a table on the index page

### Required Setup

1. **GitHub Secrets**
   Configure in repository Settings ’ Secrets and variables ’ Actions:
   - `USER_NAME`: SmartClaim test user email (required)
   - `PASSWORD`: SmartClaim test user password (required)
   - `BASE_URL`: Target environment URL (optional, defaults to dev2)

2. **GitHub Pages**
   - Enable GitHub Pages in repository settings
   - Source: GitHub Actions
   - Reports automatically published after workflow runs

### Accessing Test Reports

After workflow execution:
1. Navigate to GitHub Actions tab
2. Click on the workflow run
3. Access reports at: `https://[username].github.io/[repository-name]/`
4. View:
   - Current test results with pass/fail status
   - Screenshots captured during test execution
   - Video recordings of the entire test run
   - Historical test run data

### Workflow Permissions
The workflow requires:
- `contents: read` - Access repository code
- `pages: write` - Deploy to GitHub Pages
- `id-token: write` - Authentication for Pages deployment

### Concurrency Control
- Uses concurrency group "pages"
- Prevents multiple simultaneous deployments
- Ensures clean deployment state