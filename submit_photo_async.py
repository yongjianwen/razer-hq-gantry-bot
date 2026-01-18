import asyncio
import os

from dotenv import load_dotenv
from playwright.async_api import async_playwright

# Load environment variables
load_dotenv()
DATA_PATH = os.environ.get("DATA_PATH")
IS_HEADLESS = os.environ.get("IS_HEADLESS")
TO_SUBMIT = os.environ.get("TO_SUBMIT")


async def upload_photo(invitation_link: str, user_id: int):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=(IS_HEADLESS == "True"))  # set True when stable
        phone = p.devices["Galaxy S24"]
        context = await browser.new_context(**phone)
        page = await context.new_page()
        await page.goto(invitation_link, wait_until="networkidle")

        await page.screenshot(path=f"{DATA_PATH}/images/debug_upload_photo.png", full_page=True)

        # Click on Face Access tab
        await page.click("#faceAccessBtn")

        # Set photo input directly
        image_path = f"{DATA_PATH}/images/{user_id}.jpg"
        await page.set_input_files("#uploadImgFileRef", image_path)

        # Upload photo
        if __name__ != "__main__" and (TO_SUBMIT == "True"):
            await page.click("#confirmBtn")

        # Optional: wait to see submission confirmation
        await asyncio.sleep(3)  # time.sleep() blocks the event loop

        # May cause ❌ Error: BrowserType.launch: Target page, context or browser has been closed problem
        # await browser.close()


async def list_devices():
    async with async_playwright() as p:
        devices = p.devices.keys()
        print("Available devices:")
        for device in sorted(devices):
            print(f"  - {device}")


if __name__ == "__main__":
    asyncio.run(upload_photo(
        "https://razertp.ultimopsim.com/staticPage/index.html?token=59080FEDC68D000",
        7538898068)
    )
