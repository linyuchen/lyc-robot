import time

from src.common.bilibili.session import session
from src.common.bilibili.wbi import WBITool


async def get_my_info():
    url = 'https://api.bilibili.com/x/space/v2/myinfo'
    resp = await session.get(url)
    return resp.json()


async def check_login() -> bool:
    my_info = await get_my_info()
    return my_info['code'] == 0


async def b32_to_bv(b23tv: str) -> str:
    """
    b23.tv链接转BV链接
    """
    url = f"https://b23.tv/{b23tv}"
    url = (await session.get(url)).url
    return str(url)


async def get_video_info(bv_id: str = "", av_id: str = "") -> None | dict:
    url = ""
    if bv_id:
        url = f"http://api.bilibili.com/x/web-interface/view?bvid={bv_id}"
    elif av_id:
        url = f"http://api.bilibili.com/x/web-interface/view?aid={av_id}"
    res = await session.get(url)
    response_body = res.json().get("data", {})
    if not response_body:
        return
    video_info = {
        **response_body,
        "title": response_body["title"],
        "desc": response_body.get("desc", ""),
        "cover_url": response_body["pic"],
        "upload_time": time.strftime("%Y/%m/%d %H:%M", time.localtime(response_body["pubdate"])),
        "duration":
            f"{response_body['duration'] // 60}:{response_body['duration'] - response_body['duration'] // 60 * 60}",
        "view": response_body["stat"]["view"],
        "danmu": response_body["stat"]["danmaku"],
        "like": response_body["stat"]["like"],
        "coin": response_body["stat"]["coin"],
        "share": response_body["stat"]["share"],
        "favorite": response_body["stat"]["favorite"],
        "owner": f"{response_body['owner']['name']}",
        "owner_face": f"{response_body['owner']['face']}",
    }
    return video_info


async def get_subtitle(aid: str, cid: str):
    url = f"https://api.bilibili.com/x/player/wbi/v2?aid={aid}&cid={cid}"

    res = (await session.get(url)).json()
    subtitles = res["data"]["subtitle"]["subtitles"]
    subtitle_urls = []
    for sub_t in subtitles:
        if sub_t["lan"] in ("ai-zh", "zh-Hans"):
            subtitle_urls.append("https:" + sub_t["subtitle_url"])

    subtitle_content = []
    for subtitle_url in subtitle_urls:
        res = (await session.get(subtitle_url)).json()
        for i in res["body"]:
            subtitle_content.append(i["content"])
    subtitle = "\n".join(subtitle_content)
    return subtitle


async def get_ai_summary(cid: str, av_id: str = "", bv_id=""):
    url = "https://api.bilibili.com/x/web-interface/view/conclusion/get"
    params = {
        "cid": cid,
    }
    if av_id:
        params["aid"] = av_id
    if bv_id:
        params["bvid"] = bv_id
    params = await WBITool().add_wbi(params)
    res = (await session.get(url, params=params)).json()
    if res["code"] != 0:
        return 'AI 总结失败，' + res['message']

    return res["data"].get('model_result', {}).get("summary")
