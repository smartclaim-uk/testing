# playwright.config.py
from playwright.sync_api import Playwright, sync_playwright

reporters = [["html", {"outputFolder": "playwright-report"}]]
