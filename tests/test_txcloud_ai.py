from src.common.ai_chat.txcloud.sse import TXChatSSEClient

client = TXChatSSEClient(app_key='', prompt='输出内容不要以Markdown格式')

async def main():
    r = await client.chat('男生24岁，那他属什么')
    print(r)

import asyncio
asyncio.run(main())