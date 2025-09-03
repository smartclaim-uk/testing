# GitHub Pages Setup for Test Reports

## Quick Setup Guide

### 1. Enable GitHub Pages
1. Go to your repository → **Settings** → **Pages**
2. Under **Source**, select **GitHub Actions**
3. Save the settings

### 2. Configure Repository Secrets
Go to **Settings** → **Secrets and variables** → **Actions** and add:

- `USER_NAME`: Your test user email (e.g., `amin@dorost.nl`)  
- `PASSWORD`: Your test user password
- `BASE_URL`: Target environment URL (optional, defaults to `https://dev2.smartclaim.uk`)

### 3. Trigger the Workflow
The workflow runs automatically on:
- Push to `main` branch
- Pull requests to `main` branch  
- Manual trigger via **Actions** tab

### 4. View Test Reports
After the workflow completes, your test reports will be available at:
```
https://[your-username].github.io/[repository-name]/
```

## Workflow Features

✅ **Automated Testing**: Runs Playwright tests in headless Chromium  
✅ **Rich HTML Reports**: Detailed test reports with screenshots  
✅ **GitHub Pages**: Automatic deployment of test artifacts  
✅ **Multiple Formats**: HTML report, screenshots, and Playwright traces  
✅ **Continuous Integration**: Runs on every push and PR  

## Workflow Badge

Add this badge to your README to show test status:

```markdown
[![Test Status](https://github.com/[USERNAME]/[REPOSITORY]/actions/workflows/test-and-deploy.yml/badge.svg)](https://github.com/[USERNAME]/[REPOSITORY]/actions/workflows/test-and-deploy.yml)
```

## Troubleshooting

### Tests Fail But Report Still Deploys
This is by design - the workflow continues even if tests fail so you can see the failure report.

### Missing Screenshots  
Ensure your test creates the `screenshots/` directory and takes screenshots as needed.

### Authentication Issues
Verify your `USER_NAME` and `PASSWORD` secrets are set correctly in repository settings.

### Pages Not Loading
Check that GitHub Pages is enabled and set to use **GitHub Actions** as the source.