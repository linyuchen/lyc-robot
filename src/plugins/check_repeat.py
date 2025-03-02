import asyncio
import hashlib
import random
from collections import defaultdict

import httpx
from nonebot.plugin import PluginMetadata
from nonebot import on_message
from nonebot_plugin_alconna import UniMsg
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent

__plugin_meta__ = PluginMetadata(
    name="复读禁言",
    description="检测到复读就打断并禁言复读机，只支持QQ平台",
    usage="",
)

group_message_state = defaultdict(lambda : {
    'last_message': '',
    'user_ids': []
})

BAN_DURATION = 60 * 2

@on_message().handle()
async def _(bot: Bot, event: GroupMessageEvent):
    state = group_message_state[event.group_id]
    current_message = ''
    group_member_id = event.sender.user_id
    for msg in event.message:
        if msg.type == 'image':
            img_url = msg.data.get('url')
            async with httpx.AsyncClient() as client:
                response = await client.get(img_url)
                hasher = hashlib.md5()
                for chunk in response.iter_bytes(chunk_size=8192):
                    # 在线程池中执行同步的hash.update操作
                    await asyncio.get_running_loop().run_in_executor(
                        None,
                        hasher.update,
                        chunk
                    )
                current_message += hasher.hexdigest()
        elif msg.type == 'text':
            current_message += msg.data.get('text')
    if not current_message:
        return
    if current_message == state['last_message']:
        state['user_ids'].append(group_member_id)
        repeat_count = len(state['user_ids'])
        repeat_max = random.randint(3, 12)
        if repeat_count >= repeat_max:
            # state['repeat_count'] = 1
            # state['last_message'] = ''
            ban_duration = (repeat_count - 2)  * BAN_DURATION
            bot_info = await bot.get_group_member_info(group_id=event.group_id, user_id=int(bot.self_id))
            if bot_info.get('role') not in ['owner', 'admin']:
                return
            user_ids = state['user_ids'][2:]
            # 选一半的用户禁言
            user_ids = random.sample(user_ids, len(user_ids) // 2)
            for user_id in user_ids:
                await bot.set_group_ban(group_id=event.group_id, user_id=user_id, duration=ban_duration)
                await asyncio.sleep(1)
            await bot.send_group_msg(group_id=event.group_id, message=f'还复读？给你禁言个{ban_duration // 60}分钟!')
            state['user_ids'] = []

    else:
        state['last_message'] = current_message
        state['user_ids'] = []
