from nonebot import on_command
from nonebot.internal.adapter import Message
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from nonebot_plugin_alconna import UniMsg

__plugin_meta__ = PluginMetadata(
    name="百度搜索",
    description="百度搜索网页预览",
    usage="百度 关键字 进行百度搜索"
)

from src.common.browser.screenshot.baidu import screenshot_search_baidu
from src.plugins.common.rules import rule_args_num

baidu_screenshot_cmd = on_command("百度", force_whitespace=True, rule=rule_args_num(min_num=1))


@baidu_screenshot_cmd.handle()
async def _(params: Message = CommandArg()):
    """
    百度搜索
    """
    img_path = await screenshot_search_baidu(params.extract_plain_text())
    data = img_path.read_bytes()
    img_path.unlink()
    await baidu_screenshot_cmd.finish(await UniMsg.image(raw=data).export())
