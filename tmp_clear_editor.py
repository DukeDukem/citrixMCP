import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = context.pages[0]

        frame_locator = page.frame_locator("section[aria-label='Nachricht verfassen'] iframe")
        body = frame_locator.locator("body#tinymce")
        await body.wait_for(timeout=15000)
        await body.click()
        await page.keyboard.press("Control+A")
        await page.keyboard.press("Backspace")
        await body.evaluate("el => el.innerHTML = '<p><br></p>'")
        await page.wait_for_timeout(300)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
