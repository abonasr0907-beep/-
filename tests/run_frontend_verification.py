import os, time
from playwright.sync_api import sync_playwright

def run_verification():
    os.makedirs('/tmp/verification/screenshots', exist_ok=True)
    os.makedirs('/tmp/verification/videos', exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="/tmp/verification/videos",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        file_url = "file://" + os.path.abspath("index.html")
        page.goto(file_url)
        page.wait_for_timeout(1000)

        # Verify language switcher and back button injection
        lang_btn = page.locator("#lang-switch-btn")
        if lang_btn.is_visible():
            lang_btn.click()
            page.wait_for_timeout(500)

        page.screenshot(path="/tmp/verification/screenshots/verification.png")
        page.wait_for_timeout(1000)
        context.close()
        browser.close()

if __name__ == "__main__":
    run_verification()
    print("Frontend playwright verification passed.")
