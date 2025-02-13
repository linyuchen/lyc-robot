import asyncio
import json
from typing import Union, Literal

import httpx
import websockets

from src.common.utils.random_hash import generate_random_hash

host = 'fs.firefly.matce.cn'

ws_url = f"wss://{host}/queue/join"

speakers = []

LangType = Union[Literal['ZH'], Literal['EN'], Literal['JP'], None]


async def get_speakers():
    async with httpx.AsyncClient() as client:
        response = await client.get(f'https://{host}/info')
        info = response.json()
        speakers_str: str = info['unnamed_endpoints']['1']['parameters'][0]['python_type']['description']
        speakers_str = speakers_str.replace('Option from: ', '').replace("'", '"').replace("(", "[").replace(")", "]")
        speakers_list = json.loads(speakers_str)  # [('说话人1', '说话人1')]
        speakers_list = [i[1] for i in speakers_list]
        speakers.extend(speakers_list)


async def get_speakers_without_lang():
    if len(speakers) == 0:
        await get_speakers()
    _speakers = [i.split('_')[0] for i in speakers]
    return _speakers


def search_speaker(speaker: str, lang: LangType):
    for s in speakers:
        if s == f'{speaker}_{lang}':
            return s
        if s == speaker:
            return s


async def fs_tts(speaker: str, text: str, lang: LangType) -> str:
    for i in range(3):
        try:
            return await _fs_tts(speaker, text, lang)
        except:
            pass

    raise Exception('服务端发生错误')


async def _fs_tts(speaker: str, text: str, lang: LangType) -> str:
    err = None
    for i in range(3):
        try:
            return await _fs_tts(speaker, text, lang)
        except Exception as e:
            err = e
            pass

    raise Exception(f'服务器出现错误 {err}')


async def _fs_tts(speaker: str, text: str, lang: LangType):
    if len(speakers) == 0:
        await get_speakers()
    speaker = search_speaker(speaker, lang)
    if not speaker:
        raise Exception(f'找不到角色 {speaker}')
    session_hash = generate_random_hash(8)

    async def call_fn(fn_index: int, data: list):
        async with websockets.connect(ws_url) as websocket:
            while True:
                recv_data = await asyncio.wait_for(recv_json(websocket), 30)
                msg = recv_data.get('msg')
                if msg == 'process_completed':
                    return recv_data
                elif msg == 'send_hash':
                    send_data = {"fn_index": fn_index, "session_hash": session_hash}
                    await send_json(websocket, send_data)

                elif msg == 'send_data':
                    send_data = {"data": data, "event_data": None, "fn_index": fn_index, "session_hash": session_hash}
                    await send_json(websocket, send_data)

    # {"msg":"process_completed","output":{"data":["sft_new/Genshin_ZH/可莉/44c561ccd517f0c0.wav_part0","啦啦啦，可莉很厉害吧~ 哎呀！ 让你看看，可莉的宝物！ 好耶！ 怎，怎么这样… 凯，凯亚哥哥是怎么教的来着… 可莉的秘密武器，锵锵！ 果然是大魔王的布置，继续继续！ 第二个！打完这些大魔王就会出现了吧？"],"is_generating":false,"duration":0.0007891654968261719,"average_duration":0.0007165126679449846},"success":true}
    reference_audio_info_1 = (await call_fn(1, [speaker]))['output']['data']

    # {"msg":"process_completed","output":{"data":[{"name":"/tmp/gradio/afb03d482eb3d462df1d52dc3956b89f63173cc5/audio.wav","data":null,"is_file":true,"orig_name":"audio.wav"}],"is_generating":false,"duration":0.1503591537475586,"average_duration":0.15022662470526085},"success":true}
    reference_audio_info_2 = (await call_fn(2, [reference_audio_info_1[0]]))['output']['data'][0]

    fn_4_send_data = [
        text, True,
        {
            'name': reference_audio_info_2['name'],
            'data': f'https://{host}/file={reference_audio_info_2["name"]}',
            "is_file": True, "orig_name": "audio.wav"
        },
        reference_audio_info_1[1], 0, 90, 0.7, 1.5, 0.7, speaker]
    final_result = await call_fn(4, fn_4_send_data)
    wav_url = f'https://{host}/file=' + final_result['output']['data'][0]['name']
    return wav_url


async def send_json(ws, data: dict):
    await ws.send(json.dumps(data))


async def recv_json(ws):
    res = await ws.recv()
    return json.loads(res)


__all__ = [
    'get_speakers_without_lang',
    'fs_tts'
]

if __name__ == '__main__':
    print(asyncio.run(get_speakers_without_lang()))
    print(asyncio.run(fs_tts('可莉', '你好呀，我是可莉', 'ZH')))
