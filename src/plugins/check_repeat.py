import random
from collections import defaultdict

from nonebot.plugin import PluginMetadata
from nonebot import on_message
from nonebot_plugin_alconna import UniMsg
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent

__plugin_meta__ = PluginMetadata(
    name="复读禁言",
    description="检测到复读就打断并禁言复读机",
    usage="",
)

group_message_state = defaultdict(lambda : {'repeat_count': 0, 'last_message': ''})

@on_message().handle()
async def _(bot: Bot, event: GroupMessageEvent):
    state = group_message_state.get(event.group_id)
    if event.message.extract_plain_text().strip() == state['last_message']:
        state['repeat_count'] += 1
        repeat_max = random.randint(3, 10)
        if state['repeat_count'] >= repeat_max:
            ban_duration = repeat_max * 10
            bot_info = await bot.get_group_member_info(group_id=event.group_id, user_id=int(bot.self_id))
            if bot_info.get('role') not in ['owner', 'admin']:
                return
            await bot.set_group_ban(group_id=event.group_id, user_id=event.sender.user_id, duration=ban_duration)
            await bot.send_group_msg(group_id=event.group_id, message=f'【{event.sender.nickname}】因为复读被禁言{ban_duration}分钟')
            state['repeat_count'] = 0
            state['last_message'] = ''
