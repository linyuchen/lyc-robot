from nonebot import on_fullmatch
from nonebot.adapters.onebot.v11 import Bot
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="运行状态",
    description="查看机器人运行状态",
    usage="运行状态",
)

from src.common.state import state

state_cmd = on_fullmatch(('运行状态', 'status'))


@state_cmd.handle()
async def _(bot: Bot):
    status = await bot.get_status()
    start_time = status.get('stat', {}).get('startup_time')
    await state_cmd.finish(state(start_time))
