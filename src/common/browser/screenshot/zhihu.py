import asyncio
import tempfile
from pathlib import Path

from playwright.async_api import Page, async_playwright

from src.common.browser.utils import load_all
from src.common.browser.screenshot.base import new_page, CHROME_DATA_DIR
from src.common.utils.image import merge_images


class ZhihuPreviewer:

    @staticmethod
    async def hidden_elements(page: Page):
        await page.evaluate(
            """
            let closeLoginBtn = document.getElementsByClassName("Modal-closeButton")[0]
            if (closeLoginBtn){
                closeLoginBtn.click()
            }
            let e = document.getElementsByClassName("ContentItem-actions");
            for (let i = 0; i < e.length; i++) {
                e[i].style.display = "none";
                //e[i].remove()
            }

            """
        )

    async def screenshot_zhihu_question(self, url: str) -> Path | None:
        async with new_page(url, headless=True) as page:
            await self.hidden_elements(page)
            question = page.locator("css=.QuestionHeader .QuestionHeader-main")
            if question.count() == 0:
                return None
            question = question.first

            question_path = Path(tempfile.mktemp(suffix=".png"))
            await question.screenshot(path=question_path)
            await asyncio.sleep(1)

            answer = page.locator("css=.AnswerItem")
            if answer.count() == 0:
                return None
            answer = answer.first
            await answer.evaluate(
                """
                e = document.getElementsByClassName("AnswerItem")[0]
                e.style.paddingLeft = "30px";
                """
            )
            answer_path = Path(tempfile.mktemp(suffix=".png"))
            await answer.screenshot(path=answer_path)

            # 合并图片
            merged_path = merge_images([question_path, answer_path])
            await page.close()
            question_path.unlink()
            answer_path.unlink()
            return merged_path

    async def screenshot_zhihu_zhuanlan(self, url: str) -> Path | None:

        async with new_page(url, headless=True) as page:
            await self.hidden_elements(page)
            await load_all(page)
            author = page.locator("css=.Post-Header")
            if author.count() == 0:
                return None
            author_path = Path(tempfile.mktemp(suffix=".png"))
            await author.screenshot(path=author_path)

            content = page.locator("css=.Post-RichTextContainer")
            if not content.count():
                return None
            await content.evaluate(
                """
                e = document.getElementsByClassName("Post-RichTextContainer")[0]
                e.style.paddingTop = "50px";
                e.style.paddingLeft = "10px";
                e.style.paddingRight = "20px";
                """
            )

            content_path = Path(tempfile.mktemp(suffix=".png"))
            await content.screenshot(path=content_path)

            merged_path = merge_images([author_path, content_path])
            await page.close()
            author_path.unlink()
            content_path.unlink()
            return merged_path


class ZhihuLogin:
    def __init__(self, headless=True):
        self.browser = None
        self.page: Page | None = None
        self.headless = headless

    async def init(self):
        self.browser = await (await async_playwright().start()).chromium.launch_persistent_context(CHROME_DATA_DIR, headless=self.headless)
        self.page = await self.browser.new_page()
        await self.page.goto('https://www.zhihu.com/signin')

    async def get_qrcode(self):
        qrcode = await self.page.wait_for_selector('.Qrcode-container.smallVersion')
        qrcode_path = Path(tempfile.mktemp(suffix=".png"))
        await qrcode.screenshot(path=qrcode_path)
        return qrcode_path

    async def check_login(self):
        for i in range(180):
            await asyncio.sleep(1)
            if self.page.url == "https://www.zhihu.com/":
                return True

        raise TimeoutError("登录知乎超时")


if __name__ == '__main__':
    async def main():
        zhihu_login = ZhihuLogin()
        await zhihu_login.init()
        qrcode_path = await zhihu_login.get_qrcode()
        print(qrcode_path)
        await zhihu_login.check_login()
        print("登录成功")


    asyncio.run(main())
