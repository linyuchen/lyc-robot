import asyncio
import re
import threading
import time

from nonebot import on_command, on_message, on_fullmatch, Bot, get_plugin_config
from nonebot.params import CommandArg, Message, Event
from nonebot.permission import SUPERUSER, Permission
from nonebot.plugin import PluginMetadata
from nonebot_plugin_alconna import UniMsg, Reply
from nonebot_plugin_uninfo import Uninfo

from nonebot_plugin_waiter import waiter

from src.common.ai_chat.chat_engine import chat, set_prompt, get_prompt, clear_prompt, clear_history, \
    set_chat_model, get_current_model
from src.common.ai_chat.base import set_ai_chat_proxy
from ..common.message import get_message_image_urls
from ...common.ai_chat.utils import summary_web
from src.common.config import CONFIG
from ..common.permission import check_group_admin
from ..common.rules import is_at_me, rule_args_num
from nonebot import get_driver

__plugin_meta__ = PluginMetadata(
    name="AI聊天",
    description="让bot支持AI回复",
    usage="@机器人+聊天内容，或者#聊天内容\n设置人格 <人格设定>, 查看人格, 清除人格, 设置聊天模型, 清除记录",
)

driver = get_driver()


@driver.on_startup
async def _():
    if CONFIG.http_proxy:
        set_ai_chat_proxy(str(CONFIG.http_proxy))


wiki_cmd = on_command("百科", force_whitespace=True, permission=SUPERUSER, rule=rule_args_num(min_num=1))


@wiki_cmd.handle()
def wiki(args: Message = CommandArg()):
    wiki_cmd.send("正在为您搜索百科...")
    params = args.extract_plain_text()

    def reply():
        res = summary_web(f"https://zh.wikipedia.org/wiki/{params[0]}")
        wiki_cmd.finish(res)

    threading.Thread(target=reply, daemon=True).start()


def gen_voice(text) -> bytes | None:
    pass
    # if not config.TTS_ENABLED:
    #     return
    # from ..tts.genshinvoice_top import tts
    # # text = text.replace("喵", "")
    # if len(text) <= 60:
    #     try:
    #         voice_bytes = tts(text)
    #         return voice_bytes
    #     except Exception as e:
    #         pass


def get_url(text: str) -> str:
    pattern = re.compile(r"(https?://[A-Za-z0-9$\-_.+!*'(),%;:@&=/?#\[\]]+)")
    url = re.findall(pattern, text)
    return url[0] if url else ""


def summary_url(url: str) -> str:
    if url := get_url(url):
        result = summary_web(url)
        return result


summary_web_cmd = on_command("总结网页", force_whitespace=True, rule=rule_args_num(min_num=1))


@summary_web_cmd.handle()
def _(event: Event, args: Message = CommandArg()):
    text = ""
    if event.reply:
        text = event.reply.message.extract_plain_text()
    text += "\n" + args.extract_plain_text()
    if url := get_url(text):
        summary_web_cmd.send("正在为您总结网页...")
        result = summary_web(url)
        summary_web_cmd.finish(result + "\n\n" + url)


def get_context_id(session: Uninfo) -> str:
    if session.scene.is_group:
        context_id = session.adapter.value + "_group_" + str(session.group.id)
    else:
        context_id = session.adapter.value + "_private_" + str(session.user.id)
    return context_id


set_prompt_cmd = on_command("设置人格", force_whitespace=True)


@set_prompt_cmd.handle()
async def _(session: Uninfo, args: Message = CommandArg()):
    set_prompt(get_context_id(session), args.extract_plain_text())
    await set_prompt_cmd.finish("人格设置成功")


clear_prompt_cmd = on_fullmatch(("清除人格", "恢复人格", "清空人格", "重置人格"))


@clear_prompt_cmd.handle()
async def _(session: Uninfo):
    clear_prompt(get_context_id(session))
    await clear_prompt_cmd.finish("人格清除成功")


get_prompt_cmd = on_fullmatch("查看人格")


@get_prompt_cmd.handle()
async def _(session: Uninfo):
    await get_prompt_cmd.finish("当前人格:\n\n" + get_prompt(get_context_id(session)))


chat_records = {}

chatgpt_cmd = on_message()


@chatgpt_cmd.handle()
async def _(bot: Bot, event: Event, session: Uninfo, msg: UniMsg):
    if session.scene.is_group:
        sender_id = session.group.id
        if not is_at_me(session, msg, event):
            if not event.get_plaintext().strip().startswith('#'):
                return
    else:
        sender_id = session.user.id
        if not event.get_plaintext().strip().startswith('#'):
            return

    if time.time() - chat_records.setdefault(sender_id, 0) < 5:
        return
    chat_records[sender_id] = time.time()

    _chat_text = event.get_plaintext()
    img_urls = get_message_image_urls(msg)
    reply_img_urls = []
    reply_msgs = msg.get(Reply)
    if reply_msgs:
        reply_msg: Reply = reply_msgs[0]
        reply_img_urls = get_message_image_urls(reply_msg.msg)
        _chat_text = reply_msg.msg.extract_plain_text() + '\n' + _chat_text
    img_urls = img_urls + reply_img_urls
    ai_chat_content = [
        {
            'type': 'text',
            'text': _chat_text,
        }
    ]
    for img_url in img_urls:
        ai_chat_content.append({
            'type': 'image_url',
            'image_url': img_url,
        })
    _res = await chat(get_context_id(session), ai_chat_content)
    await bot.send(event, await (UniMsg.reply(event.message_id) + _res).export(bot))
        # voice_bytes = gen_voice(_res)
        # if voice_bytes:
        #     await bot.send(event, MessageSegment.record(voice_bytes))


clear_history_cmd = on_fullmatch("清除记录")


@clear_history_cmd.handle()
async def _(session: Uninfo):
    clear_history(get_context_id(session))
    await clear_history_cmd.finish("AI 聊天记录清除成功")


set_chat_model_cmd = on_command("设置聊天模型", aliases={'聊天模型'}, permission=check_group_admin)


@set_chat_model_cmd.handle()
async def _(session: Uninfo):
    context_id = get_context_id(session)
    models = [c.model for c in CONFIG.ai_chats]
    prompt = f'当前模型 {get_current_model(context_id)}\n\n' + '可选模型：\n'
    for index, model in enumerate(models):
        prompt += f'{index + 1}: {model}\n'
    prompt += '\n请输入数字选择模型'
    await set_chat_model_cmd.send(prompt)

    @waiter(waits=['message'], keep_session=True)
    async def check(event: Event):
        return event.get_plaintext().strip()

    async for resp in check(timeout=20):
        if resp is None:
            # await bot.delete_msg(message_id=song_list_msg_id)
            return
        if not resp.isdigit():
            continue
        model_index = int(resp)
        if model_index <= 0 or model_index > len(models):
            continue
        model = models[model_index - 1]
        set_chat_model(context_id, model)
        return await set_chat_model_cmd.finish("聊天模型设置成功")
