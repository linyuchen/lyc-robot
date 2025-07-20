import re
import asyncio

import httpx

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
        download_links = re.findall('https://.+?qqfile/qq/QQNT/[^<]+', content)
        if not download_links:
            return None, ''
        lnk_start_pos = content.find("【下载链接】")
        change_log_content = content[:lnk_start_pos]
        change_log_start_pos = change_log_content.rfind('【版本特性】')
        change_log_content = change_log_content[change_log_start_pos:]
        change_log_content = change_log_content.replace('</text>', '</text>\n')
        change_log_content = change_log_content.replace('</span>', '</span>\n')
        change_log_content = re.sub('<[^>]+?>', '', change_log_content)

        version = re.findall(r'(\d{5})_',download_links[0])[0]
        text = f'QQNT {version}\n{change_log_content}\n\n{"\n".join(download_links)}'
        return version, text

    async def get_new_version(self):
        try:
            v, content = await self.get_version()
        except Exception as e:
            return None, ''
        if v and v > self.current_version:
            self.current_version = v
            return v, content
        return None, ''


qqnt_version_monitor = QQNTVersionMonitor()

if __name__ == '__main__':

    import time
    while True:
        print(asyncio.run(qqnt_version_monitor.get_new_version())[0])
        time.sleep(5)
