import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="session")
def browser(request):
    """Browser fixture with video recording enabled"""
    headed = request.config.getoption("--headed", default=False)
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=not headed,
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