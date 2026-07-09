import json
import logging
import os

from playwright.sync_api import expect

# Configure logging for better test reporting
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = os.getenv("BASE_URL")
GENERATE_WAIT_TIMEOUT = 5  # minutes
UPLOAD_WAIT_TIMEOUT = 3  # minutes
# Ensure screenshots directory exists
os.makedirs("screenshots", exist_ok=True)


def login(page, module: str) -> None:
    """Login and navigate to the given module page."""
    logger.info("Step 1: Performing login")
    page.goto(url=f"{BASE_URL}/login")
    page.screenshot(path="screenshots/01_login_page.png")
    logger.info("✓ Navigated to login page")

    page.locator("#username").fill(os.getenv("USER_NAME"))
    page.locator("#password").fill(os.getenv("PASSWORD"))
    page.locator("form").get_by_role("button", name="Log in").click()

    # Wait for the post-login redirect to settle before touching the nav. The
    # app prerenders the login form (instant paint) and then redirects to
    # /draft once auth resolves; clicking a module link before that lands races
    # the redirect and leaves us on /draft (see global_state KeyError below).
    page.wait_for_url("**/draft")
    page.screenshot(path=f"screenshots/{module}_02_login_completed.png")
    logger.info("✓ Login completed successfully")

    page.get_by_role("link", name=module.capitalize()).click()
    # Confirm the module page is actually loaded before reading its state.
    page.wait_for_url(f"**/{module}")


def submit_and_verify(page, module: str, submodules: dict[str, list[str]]) -> None:
    """Click Submit and verify all submodule content is generated."""
    logger.info("Clicking Submit and verifying content generation")
    total = sum(len(v) for v in submodules.values())
    successful = 0
    failed: list[str] = []

    try:
        # Submit is rendered but disabled until the module is ready (e.g. all
        # files Ready), so wait for enabled rather than visible.
        submit_button = page.get_by_role("button", name="Submit")
        expect(submit_button).to_be_enabled(timeout=60 * 1000)
        submit_button.click()
        logger.info("✓ Submitted successfully")
    except Exception as e:
        logger.error(f"Submit failed: {e}")
        page.screenshot(path=f"screenshots/{module}_submit_failed.png")
        raise

    for submod, subsubmods in submodules.items():
        for subsubmod in subsubmods:
            try:
                logger.info(f"Waiting for content: {module}_{submod}_{subsubmod}")
                content_selector = f"#main-content-{module}_{submod}_{subsubmod}"
                expect(page.locator(content_selector)).not_to_contain_text(
                    "No content", timeout=GENERATE_WAIT_TIMEOUT * 60 * 1000
                )
                expect(page.locator(content_selector)).not_to_be_empty(
                    timeout=GENERATE_WAIT_TIMEOUT * 60 * 1000
                )
                logger.info(f"✓ {submod}/{subsubmod}: Content generated")
                page.screenshot(
                    path=f"screenshots/{module}_{submod}_{subsubmod}_generated.png"
                )
                successful += 1
            except Exception as e:
                logger.error(f"{submod}/{subsubmod} failed: {e}")
                page.screenshot(
                    path=f"screenshots/{module}_{submod}_{subsubmod}_failed.png"
                )
                failed.append(f"{submod}/{subsubmod}")
                continue

    logger.info(f"✓ Generated {successful}/{total} submodules")
    assert not failed, (
        f"{module}: {len(failed)}/{total} submodules did not generate content: "
        f"{', '.join(failed)}"
    )


def get_module_files(page, module: str) -> dict:
    """Read the module's files dict from the app's localStorage state."""
    global_state = json.loads(
        page.evaluate("window.localStorage.getItem('global_state')") or "{}"
    )
    files = global_state.get(module, {}).get("files", {})
    return {k: v for k, v in files.items() if k != "data"}


def wait_for_files_list(page) -> None:
    """Wait for the files table to finish its initial server load.

    Uploading while the list is still loading races the app's post-load
    cleanup sweep, which can drop the in-flight upload from its state.
    """
    page.wait_for_selector("#files-table-container", timeout=30 * 1000)
    page.wait_for_selector(
        "#files-loading-container", state="detached", timeout=60 * 1000
    )


def delete_leftover_uploads(page, module: str, file_name: str) -> None:
    """Delete leftovers of our test file from previous failed runs.

    The app silently drops uploads whose filename already exists in the
    module, so a leftover output.pdf makes every later run fail.
    """
    for file_id, entry in get_module_files(page, module).items():
        name = (entry.get("data") or {}).get("original_file_name") or ""
        if name.lower() != file_name.lower():
            continue
        logger.info(f"Deleting leftover file from previous run: {file_id}")
        page.locator(f"#delete-button-{file_id}").click()
        page.wait_for_selector(
            f"#file-row-{file_id}", state="detached", timeout=30 * 1000
        )
        logger.info(f"✓ Deleted leftover file {file_id}")


def upload_and_process(page, module: str) -> str:
    """Upload file, wait for processing, accept results. Returns file_id."""
    import time

    logger.info("Step 2: Uploading file")
    wait_for_files_list(page)
    delete_leftover_uploads(page, module, "output.pdf")
    files_before = set(get_module_files(page, module))

    page.locator("#file-upload").set_input_files("output.pdf")
    page.screenshot(path=f"screenshots/{module}_03_file_uploaded.png")
    logger.info("✓ File uploaded successfully")

    logger.info("Step 3: Waiting for file processing")
    # The state entry is created asynchronously after the change event, so
    # poll for it instead of reading global_state once.
    file_id = None
    deadline = time.time() + 30
    while time.time() < deadline:
        new_files = set(get_module_files(page, module)) - files_before
        if new_files:
            file_id = new_files.pop()
            break
        time.sleep(1)
    if not file_id:
        page.screenshot(path=f"screenshots/{module}_04_upload_not_registered.png")
        raise AssertionError(f"{module}: uploaded file never appeared in the app state")
    logger.info(f"File ID: {file_id}")

    start_time = time.time()
    max_wait_seconds = UPLOAD_WAIT_TIMEOUT * 60

    while (time.time() - start_time) < max_wait_seconds:
        try:
            current_status = page.locator(f"#status-cell-{file_id}").text_content(
                timeout=10 * 1000
            )
            logger.info(f"Processing status: {current_status}")
            if "Ready" in current_status:
                logger.info("✓ File processing completed")
                page.screenshot(
                    path=f"screenshots/{module}_04_processing_completed.png"
                )
                break
            elif "Error" in current_status or "Failed" in current_status:
                logger.error(f"Processing failed: {current_status}")
                page.screenshot(path=f"screenshots/{module}_04_processing_failed.png")
                raise AssertionError(
                    f"{module}: file processing failed: {current_status}"
                )
            time.sleep(10)
        except AssertionError:
            raise
        except Exception as e:
            logger.warning(f"Error checking status: {e}")
            time.sleep(10)
    else:
        logger.error("File processing timed out")
        page.screenshot(path=f"screenshots/{module}_04_processing_timeout.png")
        raise AssertionError(
            f"{module}: file processing did not reach Ready within "
            f"{UPLOAD_WAIT_TIMEOUT} minutes"
        )

    # Try to accept results if available
    try:
        accept_button = page.get_by_role("button", name="Accept")
        if accept_button.is_visible():
            accept_button.click()
            logger.info("✓ Accepted results")
    except Exception:
        pass

    return file_id


def cleanup_file(page, module: str, file_id: str | None) -> None:
    """Delete uploaded file if possible."""
    if not file_id:
        return
    logger.info("Attempting cleanup")
    try:
        delete_button = page.locator(f"#delete-button-{file_id}")
        delete_button.wait_for(state="visible", timeout=10 * 1000)
        delete_button.click()
        page.wait_for_selector(
            f"#file-row-{file_id}", state="detached", timeout=30 * 1000
        )
        logger.info("✓ Deleted file successfully")
        page.screenshot(path=f"screenshots/{module}_cleanup_completed.png")
    except Exception as e:
        logger.warning(f"Cleanup failed: {e}")


def per_component(page, module: str, submodules: dict[str, list[str]]) -> None:
    """Test flow for file-upload modules (draft, qualify, etc.)."""
    logger.info(f"🚀 Starting {module} test workflow")

    login(page, module)
    file_id = upload_and_process(page, module)
    try:
        submit_and_verify(page, module, submodules)
    finally:
        # Always delete the uploaded file: a leftover output.pdf poisons the
        # next run (same-name uploads are silently dropped by the app).
        cleanup_file(page, module, file_id)

    logger.info("🎉 Test execution completed!")


def per_component_textarea(
    page,
    module: str,
    submodules: dict[str, list[str]],
    sample_text: str = "Sample text for testing.",
) -> None:
    """Test flow for textarea-input modules (review)."""
    logger.info(f"🚀 Starting {module} test workflow (textarea mode)")

    login(page, module)

    # Fill textareas with sample text
    logger.info("Step 2: Filling textareas with sample text")
    textareas = page.locator("textarea")
    count = textareas.count()
    logger.info(f"Found {count} textareas")
    for i in range(count):
        textareas.nth(i).click()
        textareas.nth(i).fill(sample_text)
        textareas.nth(i).dispatch_event("input")
        textareas.nth(i).dispatch_event("change")
    page.screenshot(path=f"screenshots/{module}_03_textareas_filled.png")
    logger.info("✓ Textareas filled")

    submit_and_verify(page, module, submodules)

    logger.info("🎉 Test execution completed!")


def test_draft(page) -> None:
    per_component(
        page,
        module="draft",
        submodules={
            "questions": ["q_1", "q_2", "q_3", "q_4", "q_5", "q_6"],
        },
    )


def test_review(page) -> None:
    review_submodules = {
        "eligibility": [
            "overall_eligibility",
            "baseline_statements",
            "internet_search",
            "feedback",
            "uncertainty_check",
            "qualifying_activity",
            "risk_factors",
        ],
        "baseline": ["comprehensiveness", "focus", "phrasing", "grammar"],
        "advance": [
            "comprehensiveness",
            "focus",
            "phrasing",
            "guideline_references",
            "grammar",
        ],
        "uncertainty": [
            "comprehensiveness",
            "focus",
            "phrasing",
            "guideline_references",
            "grammar",
        ],
        "resolution": [
            "comprehensiveness",
            "focus",
            "phrasing",
            "guideline_references",
            "grammar",
        ],
        "overall": ["coherence", "competent_professionals"],
        "questions_for_client": [
            "research",
            "risk_factors",
            "narrative_content_coverage",
        ],
    }

    per_component_textarea(
        page,
        module="review",
        submodules=review_submodules,
    )


def test_qualify(page) -> None:
    submodules = {
        "eligibility": [
            "summary",
            "baseline_statements",
            "internet_search",
            "feedback",
            "uncertainty_check",
            "qualifying_activity",
            "risk_factors",
        ],
        "narrative_content_coverage": [
            "baseline",
            "advance",
            "uncertainty",
            "resolution",
        ],
        "questions_for_client": [
            "research",
            "risk_factors",
            "narrative_content_coverage",
        ],
    }

    per_component(
        page,
        module="qualify",
        submodules=submodules,
    )


if __name__ == "__main__":
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            slow_mo=500,
        )
        page = browser.new_page()
        per_component(
            page,
            module="qualify",
            submodules={"eligibility": ["summary"]},
        )
        browser.close()
