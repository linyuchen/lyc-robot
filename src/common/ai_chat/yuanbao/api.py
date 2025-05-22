import asyncio
import hmac
import json
import re
import sys
import urllib.parse
from hashlib import sha1
from pathlib import Path

import httpx


class YuanBaoApi:
    def __init__(self, hy_user: str, hy_token: str, agent_id: str):
        self.agent_id = agent_id
        self.url = 'https://yuanbao.tencent.com/api'
        self.headers = {
            'Content-Type': 'application/json',
            'Cookie': f'hy_user={hy_user}; hy_token={hy_token}; hy_source=web',
        }

    def __create_httpx_client(self):
        """
        Create an httpx client with the specified headers.
        """
        return httpx.AsyncClient(headers=self.headers)

    async def create_chat(self) -> str:
        """
        return chat id
        """
        url = f'{self.url}/user/agent/conversation/create'
        data = {
            'agentId': self.agent_id,
        }
        async with self.__create_httpx_client() as client:
            response = await client.post(url, json=data)
            if response.status_code != 200:
                raise Exception(f"Failed to create chat: {response.text}")
            return response.json()['id']

    async def chat(self, chat_id: str, content: str) -> str:
        """
        return chat response
        """
        url = f'{self.url}/chat/{chat_id}'
        data = {
            "model": "gpt_175B_0404",
            "prompt": f"{content}",
            "plugin": "Adaptive",
            "displayPrompt": f"{content}",
            "displayPromptType": 1,
            "options": {
                "imageIntention": {
                    "needIntentionModel": True,
                    "backendUpdateFlag": 2,
                    "intentionStatus": True
                }
            },
            "multimedia": [],
            "agentId": "naQivTmsDa",
            "supportHint": 1,
            "version": "v2",
            "chatModelId": "deep_seek_v3",
            "chatModelExtInfo": "{\"modelId\":\"deep_seek_v3\",\"subModelId\":\"\",\"supportFunctions\":{\"supportInternetSearch\":true,\"internetSearch\":\"supportInternetSearch\"}}",
            "supportFunctions": [
                "supportInternetSearch",
                "supportInternetSearch"
            ]
        }
        resp_text = ''
        quote_count = 0

        def remove_quotes(_resp_text: str, _quote_count: int) -> str:
            def replacer(match):
                num = int(match.group(1))
                return '' if 1 <= num <= _quote_count else match.group(0)

            return re.sub(r'\[\^(\d+)\]', replacer, _resp_text)

        client = self.__create_httpx_client()
        async with client.stream('POST', url, json=data) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data:"):
                    data = line.split("data:", 1)[1]
                    try:
                        data = json.loads(data)
                    except json.decoder.JSONDecodeError:
                        continue
                    if data.get('type') == 'text':
                        msg = data.get('msg', '')
                        print(msg, end='')
                        resp_text += msg
                    elif data.get('type') == 'searchGuid':
                        quote_count = len(data.get('docs', []))
            if quote_count:
                resp_text = remove_quotes(resp_text, quote_count)
            return resp_text

    def __generate_q_signature(
            self,
            http_method: str,
            path: str,
            query_params: dict[str, str],
            headers: dict[str, str],
            sign_time: str,
            secret_key: str,
    ) -> str:

        def url_encode(s: str, safe: str = "") -> str:
            return urllib.parse.quote(s, safe=safe)

        def canonicalize_params(params: dict[str, str]) -> str:
            normalized = {k.lower(): v for k, v in params.items()}
            sorted_items = sorted(normalized.items())
            return "&".join(f"{url_encode(k)}={url_encode(v)}" for k, v in sorted_items)

        encoded_path = url_encode(path.strip(), safe="/")

        canonical_query_string = canonicalize_params(query_params)

        canonical_headers = canonicalize_params(headers)

        format_string = (
            f"{http_method.lower()}\n" f"{encoded_path}\n" f"{canonical_query_string}\n" f"{canonical_headers}\n"
        )
        format_string_hash = sha1(format_string.encode()).hexdigest()

        string_to_sign = f"sha1\n{sign_time}\n{format_string_hash}\n"
        sign_key = hmac.new(secret_key.encode(), sign_time.encode(), sha1).hexdigest()
        signature = hmac.new(sign_key.encode(), string_to_sign.encode(), sha1).hexdigest()

        return signature

    async def upload_file(self, path: Path, is_image: bool):
        url = f'{self.url}/resource/genUploadInfo'
        data = {
            "fileName": f"{path.name}",
            "docFrom": "localDoc",
            "docOpenId": ""
        }

        resp = (await self.__create_httpx_client().post(url, json=data)).json()
        download_url = resp['resourceUrl']
        bucket = resp.get('bucketName')
        location = resp.get('location')
        secret_id = resp.get('encryptTmpSecretId')
        secret_key = resp.get('encryptTmpSecretKey')
        token = resp.get('encryptToken')
        start_time = resp.get('startTime')
        expired_time = resp.get('expiredTime')
        upload_host = f'{bucket}.cos.accelerate.myqcloud.com'
        url = f'https://{upload_host}{location}'
        content_length = str(path.stat().st_size)
        headers = {}
        headers_to_sign = {
            "content-length": content_length,
            "host": upload_host,
        }
        if is_image:
            headers["Content-Type"] = "image/png"
            pic_operations = '{"is_pic_info":1,"rules":[{"fileid":"%s","rule":"imageMogr2/format/jpg"}]}' % location
            headers["Pic-Operations"] = pic_operations
            headers_to_sign["pic-operations"] = pic_operations
        else:
            headers["Content-Type"] = "application/octet-stream"

        signature = self.__generate_q_signature("PUT", location, {}, headers_to_sign, f'{start_time};{expired_time}',
                                                secret_key)
        authorization = f'q-sign-algorithm=sha1&q-ak={secret_id}&q-sign-time={start_time};{expired_time}&q-key-time={start_time};{expired_time}&q-header-list=content-length;host{";pic-operations" if is_image else ''}&q-url-param-list=&q-signature={signature}'
        headers.update({
            "Host": upload_host,
            "Content-Length": content_length,
            "Origin": "https://yuanbao.tencent.com",
            "Referer": "https://yuanbao.tencent.com/",
            "User-Agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
            "x-cos-security-token": token,
            "Authorization": authorization,
        })
        client = httpx.AsyncClient(headers=headers)
        resp = await client.put(url, content=path.read_bytes(), headers=headers)
        resp_xml = resp.text
        return download_url


if __name__ == '__main__':
    t = YuanBaoApi(hy_user=sys.argv[1], hy_token=sys.argv[2], agent_id=sys.argv[3])


    async def test():
        # chat_id = await t.create_chat()
        # print(chat_id)
        # print(await t.chat(chat_id, '请给我一份关于python的介绍'))
        await t.upload_file(Path('example.png'), True)


    asyncio.run(test())
