from nonebot.plugin import PluginMetadata
from nonebot import on_message
from nonebot_plugin_uninfo import Uninfo, SupportAdapter
from nonebot_plugin_alconna import UniMsg
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent

__plugin_meta__ = PluginMetadata(
    name="复读禁言",
    description="检测到复读就打断并禁言复读机",
    usage="",
)

group_message_state = {}

@on_message().handle()
async def _(bot: Bot, event: GroupMessageEvent):
    await bot.get_group_member_info(group_id=event.group_id, user_id=int(bot.self_id))