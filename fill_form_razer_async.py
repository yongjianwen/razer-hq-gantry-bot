import asyncio
import os

from dotenv import load_dotenv
from playwright.async_api import async_playwright

# Load environment variables
load_dotenv()
DATA_PATH = os.environ.get("DATA_PATH")
FORM_URL = os.environ.get("FORM_URL")
NAME_PLACEHOLDER = os.environ.get("NAME_PLACEHOLDER")
EMAIL_PLACEHOLDER = os.environ.get("EMAIL_PLACEHOLDER")
DEST_PLACEHOLDER = os.environ.get("DEST_PLACEHOLDER")
DEST_INPUT = os.environ.get("DEST_INPUT")
IS_HEADLESS = os.environ.get("IS_HEADLESS")
TO_SUBMIT = os.environ.get("TO_SUBMIT")


async def fill_and_submit(name: str, email: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=(IS_HEADLESS == "True"))  # set True when stable
        page = await browser.new_page()
        await page.goto(FORM_URL, wait_until="networkidle")

        await page.screenshot(path=f"{DATA_PATH}/images/debug_empty_form.png", full_page=True)

        # Fill text inputs
        await page.get_by_placeholder(NAME_PLACEHOLDER).fill(name)
        await page.get_by_placeholder(EMAIL_PLACEHOLDER).fill(email)

        # Select dropdown option
        await page.get_by_placeholder(DEST_PLACEHOLDER).click()
        await page.get_by_role("option", name=DEST_INPUT).click()

        # Submit the form
        if __name__ != "__main__" and (TO_SUBMIT == "True"):
            await page.click(".submit-btn")

        # Optional: wait to see submission confirmation
        await asyncio.sleep(3)  # time.sleep() blocks the event loop

        # May cause ❌ Error: BrowserType.launch: Target page, context or browser has been closed problem
        # await browser.close()


if __name__ == "__main__":
    print("This only runs when executed directly")
    asyncio.run(fill_and_submit("Lim Yew Chinn", "limyewchinn@gmail.com"))
