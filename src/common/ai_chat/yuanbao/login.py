import asyncio
import tempfile
from pathlib import Path
from typing import TypedDict

from playwright.async_api import async_playwright, BrowserContext, Page


class Cookie(TypedDict):
    hy_user: str
    hy_token: str
    client_id: str


class TXYuanBaoLogin:

    def __init__(self):
        self.browser: BrowserContext | None = None
        self.page: Page | None = None

    async def init(self):
        browser_context_manager = await async_playwright().start()
        self.browser = await browser_context_manager.chromium.launch_persistent_context(
            tempfile.mkdtemp(),
            headless=True)
        self.page = await self.browser.new_page()
        await self.page.goto("https://yuanbao.tencent.com/")

    async def get_qrcode(self) -> Path:
        try:
            login_btn = await self.page.wait_for_selector('.agent-dialogue__tool__login')
            await login_btn.click()
            await asyncio.sleep(1.5)
            (await self.page.wait_for_selector('.hyc-login__switch-type .t-radio-button'))
            login_by_qq_btn = (await self.page.query_selector_all('.hyc-login__switch-type .t-radio-button'))[-1]
            async with self.page.expect_navigation():
                await login_by_qq_btn.click()
            # tmp_path = tempfile.mktemp(suffix=".png")
            iframe = self.page.frames[-1]
            qrcode = await iframe.wait_for_selector('.qrlogin_img_out')
        except Exception as e:
            raise TimeoutError("获取登录二维码超时")
        tmp_path = tempfile.mktemp(suffix=".png")
        await qrcode.screenshot(path=tmp_path)
        return Path(tmp_path)

    async def __get_cookie(self) -> Cookie | None:
        cookies = await self.browser.cookies()
        if not list(filter(lambda cookie: cookie['name'] == 'ptcz', cookies)):
            return None
        result: Cookie = {
            'hy_user': '',
            'hy_token': '',
            'client_id': 'naQivTmsDa',
        }
        for cookie in cookies:
            if cookie['name'] == 'hy_user':
                result['hy_user'] = cookie['value']
            if cookie['name'] == 'hy_token':
                result['hy_token'] = cookie['value']

        return result

    async def get_cookie(self) -> Cookie:
        for i in range(120):
            await asyncio.sleep(1)
            cookie = await self.__get_cookie()
            if cookie:
                return cookie
        raise TimeoutError("获取元宝登录cookie超时")

    async def close(self):
        await self.page.close()
        await self.browser.close()


if __name__ == '__main__':
    async def main():
        login = TXYuanBaoLogin()
        await login.init()
        qrcode_path = await login.get_qrcode()
        print(qrcode_path)
        print(await login.get_cookie())
        await login.close()

    asyncio.run(main())
