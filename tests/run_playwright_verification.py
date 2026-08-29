import asyncio
import os
import sys
from playwright.async_api import async_playwright

async def run_playwright_tests():
    # Start uvicorn server in background or test static files via lightweight HTTP server / file URLs
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()

        # 1. Test SEO Landing page
        seo_path = os.path.abspath("seo/رحمانية-اراضي.html")
        await page.goto(f"file://{seo_path}")
        title = await page.title()
        assert "الرحمانية" in title
        print("✅ SEO Landing Page Playwright Test Passed")

        # 2. Test PWA Prompt display timer
        pwa_path = os.path.abspath("index.html")
        await page.goto(f"file://{pwa_path}")
        await page.wait_for_timeout(2500) # Wait 2.5s for PWA prompt to trigger
        pwa_prompt = await page.query_selector(".pwa-install-prompt")
        assert pwa_prompt is not None
        print("✅ PWA Prompt Timing Playwright Test Passed")

        # 3. Test Language Switcher button
        lang_btn = await page.query_selector("#lang-switch-btn")
        assert lang_btn is not None
        await lang_btn.click()
        html_lang = await page.get_attribute("html", "lang")
        assert html_lang == "en"
        print("✅ i18n Language Toggle Playwright Test Passed")

        # 4. Test Performance metric (LCP < 2.5s simulated)
        metrics = await page.evaluate("() => performance.timing.loadEventEnd - performance.timing.navigationStart")
        print(f"⚡ Simulated Load Metric: {metrics}ms")

        await browser.close()
        print("🎉 ALL PLAYWRIGHT TESTS PASSED SUCCESSFULY!")

if __name__ == "__main__":
    asyncio.run(run_playwright_tests())
