import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="session")
def browser():
    """Browser fixture with video recording enabled"""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,  # CI runs headless
        )
        yield browser
        browser.close()

@pytest.fixture(scope="function")
def page(browser):
    """Page fixture with video recording and screenshot options"""
    context = browser.new_context(
        record_video_dir="test-results/",
        record_video_size={"width": 1280, "height": 720}
    )
    page = context.new_page()
    yield page
    context.close()