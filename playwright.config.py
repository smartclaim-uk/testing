# playwright.config.py
from playwright.sync_api import Playwright, sync_playwright

reporters = [["html", {"outputFolder": "playwright-report"}]]

# Playwright test configuration
def pytest_configure(config):
    config.option.video = "on"
    config.option.screenshot = "on"
