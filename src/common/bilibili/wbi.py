import time
import functools
import urllib.parse
from hashlib import md5
from src.common.bilibili.session import session

mixinKeyEncTab = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52
]


class WBITool:

    def __get_mixin_key(self, orig: str):
        return functools.reduce(lambda s, i: s + orig[i], mixinKeyEncTab, '')[:32]

    def __enc_wbi(self, params: dict, img_key: str, sub_key: str):
        mixin_key = self.__get_mixin_key(img_key + sub_key)
        curr_time = round(time.time())
        params['wts'] = curr_time  # 添加 wts 字段
        params = dict(sorted(params.items()))  # 按照 key 重排参数
        # 过滤 value 中的 "!'()*" 字符
        params = {
            k: ''.join(filter(lambda c: c not in "!'()*", str(v)))
            for k, v
            in params.items()
        }
        query = urllib.parse.urlencode(params)  # 序列化参数
        wbi_sign = md5((query + mixin_key).encode()).hexdigest()  # 计算 w_rid
        params['w_rid'] = wbi_sign
        return params


    async def __get_wbi_keys(self) -> tuple[str, str]:
        resp = await session.get('https://api.bilibili.com/x/web-interface/nav')
        resp.raise_for_status()
        json_content = resp.json()
        img_url: str = json_content['data']['wbi_img']['img_url']
        sub_url: str = json_content['data']['wbi_img']['sub_url']
        img_key = img_url.rsplit('/', 1)[1].split('.')[0]
        sub_key = sub_url.rsplit('/', 1)[1].split('.')[0]
        return img_key, sub_key

    async def add_wbi(self, params: dict):
        img_key, sub_key = await self.__get_wbi_keys()
        params = self.__enc_wbi(params, img_key, sub_key)
        return params
