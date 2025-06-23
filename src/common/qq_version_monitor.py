import re
import asyncio

import httpx
from bs4 import BeautifulSoup

url = "https://docs.qq.com/doc/DVXNoRlpKaWhEY015?nlc=1"

class QQNTVersionMonitor:
    current_version = ''

    async def init(self):
        await self.get_new_version()

    async def get_version(self):
        client = httpx.AsyncClient()
        response = await client.get(url)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch the page: {response.text}")
        content = response.text
        # 使用beautifulsoup4解析HTML内容，获取class="melo-page-view"的div
        soup = BeautifulSoup(content, 'html.parser')
        div_elements = soup.find_all('div', class_='melo-paragraph')
        # 获取div的文本，并且处理换行
        text = ''
        # 跳过第一个div，因为它通常是标题或不需要的内容
        for div in div_elements[1:]:
            lines = []
            for child in div.children:
                if getattr(child, 'name', None) == 'span':
                    lines.append(child.get_text(strip=True))
                elif hasattr(child, 'get_text'):
                    lines.append('\n' + child.get_text(strip=True))
                elif isinstance(child, str):
                    lines.append(child.strip())
            text += ''.join(lines)
        # print(text)
        # 使用正则匹配第一个日期
        match = re.search(r'\.(\d{5})_x64\.exe', text)
        version = match.group(1) if match else None
        return version, text

    async def get_new_version(self):
        try:
            v, content = await self.get_version()
        except Exception as e:
            return None, ''
        if v != self.current_version:
            self.current_version = v
            return v, content
        return None, ''


qqnt_version_monitor = QQNTVersionMonitor()

if __name__ == '__main__':
    asyncio.run(qqnt_version_monitor.get_version())
