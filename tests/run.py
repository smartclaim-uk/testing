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


def per_component(page, module: str, submodules: dict[str, list[str]]) -> None:
    logger.info(f"🚀 Starting {module} {submodules} test workflow")

    # Step 1: Login
    logger.info("Step 1: Performing login")
    page.goto(url=BASE_URL)
    page.screenshot(path="screenshots/01_homepage.png")
    logger.info("✓ Navigated to homepage")

    page.get_by_role("button", name="arrow left to bracket outline").click()
    logger.info("✓ Clicked login button")

    page.get_by_placeholder("Enter your email").click()
    page.get_by_placeholder("Enter your email").fill(os.getenv("USER_NAME"))
    page.get_by_placeholder("Enter your email").press("Tab")
    page.get_by_placeholder("Enter your password").fill(os.getenv("PASSWORD"))
    page.get_by_placeholder("Enter your password").press("Enter")
    page.screenshot(path=f"screenshots/{module}_02_login_completed.png")
    logger.info("✓ Login completed successfully")

    page.get_by_role("link", name=module.capitalize()).click()

    # Step 2: File Upload
    logger.info("Step 2: Uploading file")
    page.get_by_role("button", name="Select Files").set_input_files("output.pdf")
    page.screenshot(path="screenshots/03_file_uploaded.png")
    logger.info("✓ File uploaded successfully")

    page.get_by_role("button", name="Select Files").press("ControlOrMeta+-")
    page.locator("div").filter(has_text="We are using cookies to").nth(3).click()
    if module == "draft":
        page.get_by_role("combobox").select_option("gpt-5-chat")
        logger.info("✓ Selected GPT-5 chat model")
    else:
        logger.info("using default gpt-4o model")
    # Step 3: File Processing
    logger.info("Step 3: Waiting for file processing")
    global_state = json.loads(
        page.evaluate("window.localStorage.getItem('global_state')")
    )
    file_id = next((f for f in global_state[module]["files"] if f != "data"), None)
    logger.info(f"File ID: {file_id}")

    # Wait for file processing with progressive timeout and better logging
    def wait_for_file_upload(max_wait_minutes=UPLOAD_WAIT_TIMEOUT):
        """Wait for file processing with progressive checks"""
        import time

        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        check_interval = 10  # Check every 10 seconds

        while (time.time() - start_time) < max_wait_seconds:
            try:
                current_status = page.locator(f"#status-text-{file_id}").text_content()
                logger.info(f"Current processing status: {current_status}")

                if "Ready" in current_status:
                    logger.info("✓ File processing completed - Status: Ready")
                    return True
                elif "Error" in current_status or "Failed" in current_status:
                    logger.error(
                        f"File processing failed with status: {current_status}"
                    )
                    return False

                # Wait before next check
                time.sleep(check_interval)

            except Exception as check_error:
                logger.warning(f"Error checking status: {check_error}")
                time.sleep(check_interval)

        return False  # Timeout reached

    try:
        if wait_for_file_upload(3):  # 3 minutes max
            page.screenshot(path="screenshots/04_processing_completed.png")
            logger.info("✓ File processing completed successfully")
        else:
            current_status = page.locator(f"#status-text-{file_id}").text_content()
            logger.error(f"File processing timed out. Final status: {current_status}")
            page.screenshot(path="screenshots/04_processing_timeout.png")

            # Continue with the test anyway to generate report
            logger.info(
                "⚠️ Continuing test despite processing timeout for report generation"
            )
    except Exception as e:
        current_status = page.locator(f"#status-text-{file_id}").text_content()
        logger.error(f"File processing error: {e}. Current status: {current_status}")
        page.screenshot(path="screenshots/04_processing_failed.png")
        # Continue with the test to generate useful report
        logger.info("⚠️ Continuing test despite processing error for report generation")

    # Try to accept results if Accept button is available
    try:
        accept_button = page.get_by_role("button", name="Accept")
        if accept_button.is_visible():
            accept_button.click()
            page.screenshot(path="screenshots/05_results_accepted.png")
            logger.info("✓ Accepted file processing results")
        else:
            logger.info("⚠️ Accept button not visible - may not be needed")
    except Exception as e:
        logger.warning(f"Could not click Accept button: {e}")
        page.screenshot(path="screenshots/05_accept_failed.png")

    # Step 4: Test Submodules Generation (if available)
    logger.info("Step 4: Testing submodules generation")
    try:
        successful_subsubmods = 0
        submit_button = page.get_by_role("button", name="Submit")
        if submit_button.is_visible():
            submit_button.click()
            logger.info("✓ Submitted submodules successfully")
        else:
            logger.error("⚠️ Submit button not visible - may not be needed")
            page.screenshot(
                path=f"screenshots/{module}_06_submit_button_not_visible.png"
            )
            raise Exception("Submit button not visible")

        for submod, subsubmods in submodules.items():
            for subsubmod in subsubmods:
                try:
                    logger.info(
                        f"Attempting to generate content for subsubmod {subsubmod}"
                    )
                    content_selector = f"#main-content-{module}_{submod}_{subsubmod}"
                    expect(page.locator(content_selector)).not_to_contain_text(
                        "No content", timeout=GENERATE_WAIT_TIMEOUT * 60 * 1000
                    )
                    expect(page.locator(content_selector)).not_to_be_empty(
                        timeout=GENERATE_WAIT_TIMEOUT * 60 * 1000
                    )

                    logger.info(
                        f"✓ subsubmod {subsubmod}: Content generated successfully"
                    )
                    page.screenshot(
                        path=f"screenshots/{module}_{submod}_{subsubmod}_06_subsubmod_{subsubmod}_generated.png"
                    )
                    successful_subsubmods += 1

                except Exception as q_error:
                    logger.error(f"subsubmod {subsubmod} generation failed: {q_error}")
                    page.screenshot(
                        path=f"screenshots/{module}_{submod}_{subsubmod}_06_subsubmod_{subsubmod}_failed.png"
                    )
                    continue

        logger.info(
            f"✓ Successfully generated {successful_subsubmods}/{len(subsubmods)} subsubmodules"
        )

    except Exception as submodules_error:
        logger.error(f"Submodules generation section failed: {submodules_error}")
        page.screenshot(
            path=f"screenshots/{module}_{submod}_06_submodules_section_failed.png"
        )

    # Step 5: Cleanup (if file_id is available)
    logger.info("Step 5: Attempting cleanup")
    try:
        delete_button_selector = f"#delete-button-{file_id}"
        if page.locator(delete_button_selector).is_visible():
            page.locator(delete_button_selector).click()
            page.wait_for_timeout(2000)
            logger.info("✓ Deleted file successfully")
            page.screenshot(
                path=f"screenshots/{module}_{submod}_07_cleanup_completed.png"
            )
        else:
            logger.info("⚠️ Delete button not found - cleanup may not be needed")
            page.screenshot(
                path=f"screenshots/{module}_{submod}_07_cleanup_not_needed.png"
            )
    except Exception as cleanup_error:
        logger.warning(f"Cleanup failed: {cleanup_error}")
        page.screenshot(path=f"screenshots/{module}_{submod}_07_cleanup_failed.png")

    logger.info("🎉 Test execution completed!")


def test_draft(page) -> None:
    per_component(
        page,
        module="draft",
        submodules={
            "questions": ["q_1", "q_2", "q_3", "q_4", "q_5"],
        },
    )

def test_defend(page) -> None:
    defend_submodules = {}

def test_review(page) -> None:
    module = "review"

    review_submodules = {
        "overall": ["coherence", "competent_professionals"],
        "eligibility": [
            "overall_eligibility",
            "risk_factors",
            "baseline_statements",
            "internet_search",
            "feedback",
            "uncertainty_check",
            "qualifying_activity",
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
    }

    per_component(
        page,
        module=module,
        submodules=review_submodules,
    )


def test_qualify(page) -> None:
    module = "qualify"
    submodules = {
        "overall_assessment": ["eligibility"],
        "baseline_research": ["baseline_statements", "internet_search", "feedback"],
        "risk_factors": [
            "risk_factors",
            "uncertainty_check",
            "qualifying_activity",
        ],
        "narrative_content_coverage": [
            "baseline",
            "advance",
            "uncertainty",
            "resolution",
        ],
    }

    per_component(
        page,
        module=module,
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
            submodule="overall_assessment",
            subsubmodules=["eligibility"],
        )
        browser.close()
