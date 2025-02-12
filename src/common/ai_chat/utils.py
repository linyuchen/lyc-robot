import requests

from src.common.ai_chat.chat_engine import chat
from src.common.utils.htmlhelper import html2txt


async def trans2en(text: str) -> str:
    return await chat("", f'将下面的文字翻译成英文，如果已经是英文则不翻译: {text}')


def summary_web(link: str) -> str:
    url = link
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        # "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "zh-CN,zh;",
        # "Sec-Ch-Ua-Platform": "Windows",
        # 'Sec-Ch-Ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        # "Sec-Fetch-Dest": "document",
        # "Accept-Encoding": "gzip, deflate, br",
        # "Connection:"keep-alive"
    }
    try:
        html = requests.get(url, headers=headers, timeout=30).text
    except Exception as e:
        return f"网页分析失败, {e}"
    text = html2txt(html).replace("\n", "")
    res = chat("", "#总结以下内容，如果不是中文就翻译成中文：\n" + text)
    return res
