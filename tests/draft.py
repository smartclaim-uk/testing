import os
import json
import logging
from playwright.sync_api import expect

# Configure logging for better test reporting
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = os.getenv("BASE_URL")


def test_draft_submit(page) -> None:
    logger.info("🚀 Starting SmartClaim test workflow")
    
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
    page.screenshot(path="screenshots/02_login_completed.png")
    logger.info("✓ Login completed successfully")
    
    # Step 2: File Upload
    logger.info("Step 2: Uploading file")
    page.get_by_role("button", name="Select Files").set_input_files("output.pdf")
    page.screenshot(path="screenshots/03_file_uploaded.png")
    logger.info("✓ File uploaded successfully")
    
    page.get_by_role("button", name="Select Files").press("ControlOrMeta+-")
    page.locator("div").filter(has_text="We are using cookies to").nth(3).click()
    page.get_by_role("combobox").select_option("gpt-5-chat")
    logger.info("✓ Selected GPT-5 chat model")
    
    # Step 3: File Processing
    logger.info("Step 3: Waiting for file processing")
    global_state = json.loads(page.evaluate("window.localStorage.getItem('global_state')"))
    file_id = next((f for f in global_state["draft"]['files'] if f!="data"), None)
    logger.info(f"File ID: {file_id}")

    expect(page.locator(f"#status-text-{file_id}")).to_contain_text("Ready", timeout=60000)
    page.screenshot(path="screenshots/04_processing_completed.png")
    logger.info("✓ File processing completed - Status: Ready")
    
    page.get_by_role("button", name="Accept").click()
    page.screenshot(path="screenshots/05_results_accepted.png")
    logger.info("✓ Accepted file processing results")

    # Step 4: Test Questions Generation
    logger.info("Step 4: Testing question generation")
    questions = [1, 2, 3, 4, 5]
    
    for q_num in questions:
        logger.info(f"Generating content for Question {q_num}")
        page.locator(f"#regenerate-button-draft_questions_q_{q_num}").click()
        expect(page.locator(f"#main-content-draft_questions_q_{q_num}")).not_to_contain_text("No content", timeout=10000)
        expect(page.locator(f"#main-content-draft_questions_q_{q_num}")).not_to_be_empty(timeout=10000)
        logger.info(f"✓ Question {q_num}: Content generated successfully")
        page.screenshot(path=f"screenshots/06_question_{q_num}_generated.png")

    # Step 5: Cleanup
    logger.info("Step 5: Cleaning up test data")
    page.locator(f"#delete-button-{file_id}").click()
    page.wait_for_timeout(2000)
    logger.info("✓ Deleted file successfully")
    page.screenshot(path="screenshots/07_cleanup_completed.png")
    
    logger.info("🎉 Test completed successfully!")

    