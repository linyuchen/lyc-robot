import tempfile
from pathlib import Path

from src.common.browser.screenshot.base import new_page


async def screenshot_github_readme(url: str, http_proxy: str = "") -> Path | None:
    async with new_page(url, http_proxy, headless=True) as page:
        e = page.locator("css=.markdown-body")
        if e.count() == 0:
            return None
        await e.evaluate(
            """
            let readme = document.getElementsByClassName("markdown-body")[0]
            readme.style.padding = "40px";
            let nav = document.querySelector("nav[aria-label='Repository files']")
            nav.parentElement.remove()
            """
        )
        path = Path(tempfile.mktemp(suffix=".png"))
        await e.screenshot(path=path)
        await page.close()
        return path
