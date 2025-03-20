import json
import uuid
from typing import TypedDict

import httpx

url = 'https://wss.lke.cloud.tencent.com/v1/qbot/chat/sse'


class TypeQuote(TypedDict):
    index: int
    position: int


class TXChatSSEClient:
    def __init__(self, app_key: str, session_id: str = None, prompt: str = ''):
        self.app_key = app_key
        self.visitor_biz_id = 'lyc-bot'
        self.session_id = session_id or str(uuid.uuid4())
        self.prompt = prompt

    async def chat(self, content: str, rm_quote=True) -> str:
        req_data = {
            'content': content,
            'bot_app_key': self.app_key,
            'visitor_biz_id': self.visitor_biz_id,
            'session_id': self.session_id,
            'system_role': self.prompt
        }
        resp_content = ''
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream('POST', url, data=json.dumps(req_data)) as resp:
                quotes: list[TypeQuote] = []
                async for line in resp.aiter_lines():
                    if line.startswith("data:"):
                        data = line.split("data:", 1)[1]
                        data = json.loads(data)
                        # if data['payload']['is_final']:
                        resp_content = data['payload'].get('content', '')
                        quote_info = data['payload'].get('quote_infos')
                        quotes.extend(data['payload'].get('quote_infos') or [])
        if rm_quote and quotes:
            old_content = resp_content
            new_content = ''

            last_quote_position = 0
            for quote in quotes:
                new_content += old_content[last_quote_position:quote['position'] - 1]
                last_quote_position = quote['position'] + 1
            resp_content = new_content
        return resp_content.strip()
