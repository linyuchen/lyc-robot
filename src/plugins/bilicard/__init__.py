import json
import time

from nonebot import Bot, on_command, on_message
from nonebot.adapters import Event
from nonebot.plugin import PluginMetadata
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot_plugin_alconna import UniMsg, SupportAdapter
from nonebot_plugin_uninfo import Uninfo
from nonebot.adapters.onebot.v11.message import MessageSegment

from src.common.bilibili.login import BiliLogin
from src.common.bilibili.session import set_bili_cookie
from src.common.bilibili.api import check_login, get_video_info, b32_to_bv, get_ai_summary
from src.common.bilibili.utils import check_is_b23, get_bv_id, get_av_id

__plugin_meta__ = PluginMetadata(
    name="B站链接",
    description="B站视频链接解析",
    usage="直接发送B站视频链接即可\n主人命令：设置B站cookie <cookies>，或直接发送 登录B站",
)


from src.common.bilicard import bilicard

cached = {}


def check_in_cache(bv_id):
    if bv_id in cached and time.time() - cached[bv_id] < 60:
        return True
    cached[bv_id] = time.time()
    return False


@on_message().handle()
async def _(session: Uninfo, event: Event, bot: Bot):
    is_group = session.scene.is_group
    msg_text = event.get_plaintext()
    if not msg_text:
        if event.get_message()[0].type == 'json': # 卡片消息
            card_json_str = event.get_message()[0].data.get('data')
            if card_json_str:
                card_json = json.loads(card_json_str)
                if 'com.tencent.miniapp' in card_json.get('app'):
                    msg_text = card_json.get('meta', {}).get('detail_1', {}).get('qqdocurl', '')

    b32_url = check_is_b23(msg_text)
    if b32_url:
        msg_text = await b32_to_bv(b32_url[0])

    bvid = get_bv_id(msg_text)
    avid = get_av_id(msg_text)

    if bvid or avid:
        if bvid and len(bvid) < 6:
            return
        if avid and len(avid) < 6:
            return

        if bvid and check_in_cache(bvid):
            return
        video_info = await get_video_info(bvid, avid)

        bvid = video_info.get("bvid", "")
        if check_in_cache(bvid + str(session.group.id) if is_group else str(session.user.id)):
            return
        img = await bilicard.gen_image(video_info)
        ai_summary = await get_ai_summary(video_info["cid"], video_info["aid"])
        # 没有简介内容或者简介等于标题的，且是卡片分享的，而且AI无法总结的就不需要发送了
        # if ((len(video_info["desc"]) < 4 or video_info["desc"] == video_info["title"])
        #         and not ai_summary):
        #     return
        if ai_summary:
            summary = "AI总结：" + ai_summary
        elif await check_login():
            summary = "AI总结：此视频不支持"
        else:
            summary = "AI总结：未登录B站，无法总结"

        url = f"https://bilibili.com/video/{bvid}" if bvid else f"https://bilibili.com/video/av{avid}"
        video_desc = "视频简介：" + video_info["desc"] + "\n\n" + summary
        if img:
            if session.adapter == SupportAdapter.onebot11 and (ai_summary or len(video_desc) > 30):
                send_msg = MessageSegment.image(img) + MessageSegment.text(url)
                await bot.send(event, send_msg)
                await bot.call_api('send_group_forward_msg', **{
                    'group_id': session.group.id,
                    'messages': [
                        {
                            'type': 'node',
                            'data': {
                                'content': {
                                    'type': 'text',
                                    'data': {
                                        'text': video_desc
                                    }
                                }
                            }
                        }
                    ]
                })
            else:
                reply_msg = UniMsg.image(raw=img) + UniMsg.text(url) + \
                            UniMsg.text(video_desc)
                await bot.send(event, await reply_msg.export())


set_cookie_cmd = on_command('设置B站cookie', permission=SUPERUSER)
login_cmd = on_command('登录B站', aliases={'登录b站', 'B站登录', 'b站登录'}, permission=SUPERUSER)

@set_cookie_cmd.handle()
async def _(args = CommandArg()):
    msg_text = args.extract_plain_text()
    if not msg_text:
        await set_cookie_cmd.finish("请在命令后输入cookie")
    set_bili_cookie(msg_text)
    await set_cookie_cmd.finish("设置成功")


@login_cmd.handle()
async def _():
    bili_login = BiliLogin()
    await bili_login.init()
    try:
        qrcode_path = await bili_login.get_qrcode()
        await login_cmd.send(await UniMsg.image(raw=qrcode_path.read_bytes()).export())
        qrcode_path.unlink()
    except Exception as e:
        return await login_cmd.finish(str(e))

    try:
        cookies = await bili_login.get_cookie()
        set_bili_cookie(cookies)
        return await login_cmd.finish("登录成功")
    except TimeoutError as e:
        return await login_cmd.finish(str(e))