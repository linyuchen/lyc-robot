import asyncio
import sys

from src.common.ai_chat.base import AIChat, Messages


async def t():
    c = AIChat(api_key=' '.join(sys.argv[1:]), model='腾讯元宝/deepseek-r1-search')
    content: Messages = [
        {
            'type': 'text',
            'text': '这是什么'
        },
        {
            'type': 'image_url',
            'image_url': 'https://hunyuan.tencent.com/api/resource/download?resourceId=a77309b63ccf48410c0632dea38ab745'
        }
    ]
    r = await c.chat(content)
    print(r)


asyncio.run(t())
