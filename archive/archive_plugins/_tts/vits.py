import gradio_client
import requests

from config import VITS_HTTP_API
from .utils import wav2silk_base64

root_url = VITS_HTTP_API
session = requests.Session()
session.timeout = 10
# 设置gradio代理
client = gradio_client.Client("http://127.0.0.1:7861")


def tts(text):
    # res_base64 = session.post(root_url + "/tts/tencent", json={"text": text, "speaker": "可莉"}).json()
    # return res_base64.get("data")
    res = client.predict(text, "中文", "可莉", 0.6, 0.66, 1.2, fn_index=0)
    wav_path = res[1]
    data = wav2silk_base64(wav_path)
    return data


if __name__ == '__main__':
    print(tts("测试"))
    # pprint(rs)
