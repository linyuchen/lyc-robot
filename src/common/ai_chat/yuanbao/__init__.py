import httpx
import litellm
from .api import YuanBaoApi, Media

session_id_map = {

}

class TXYuanBao(litellm.CustomLLM):
    async def acompletion(self, *args, **kwargs):
        app_key = kwargs.get('api_key')
        hy_user, hy_token, agent_id = app_key.split()
        session_id = kwargs.get('optional_params').get('session_id')
        messages = kwargs.get('messages', [])
        prompt = ''
        media_list: list[Media] = []
        image_urls = []
        prompt = ''
        for message in messages:
            if message['role'] == 'system':
                prompt += message['content'] + '\n'

        ori_content = messages[-1]['content']
        content = ''
        if isinstance(ori_content, list):
            for c in ori_content:
                if isinstance(c, dict):
                    if c.get('type') == 'text':
                        content += c['text'] + '\n'
                    elif c.get('type') == 'image_url':
                        image_urls.append(c['image_url'])
        else:
            content = ori_content

        client = YuanBaoApi(hy_user, hy_token, agent_id)
        for url in image_urls:
            image_bytes = (await httpx.AsyncClient().get(url)).read()
            media = await client.upload_file(image_bytes)
            media_list.append(media)

        if session_id not in session_id_map:
            yuanbao_session_id = await client.create_chat()
            session_id_map[session_id] = yuanbao_session_id
            session_id = yuanbao_session_id
        else:
            session_id = session_id_map[session_id]

        return await client.chat(session_id, content, media_list)