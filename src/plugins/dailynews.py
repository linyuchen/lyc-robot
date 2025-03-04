import httpx
from nonebot import on_fullmatch
from nonebot.internal.adapter import Message
from nonebot.plugin import PluginMetadata
from nonebot_plugin_alconna import UniMsg


__plugin_meta__ = PluginMetadata(
    name="每日新闻",
    description="查看今日新闻",
    usage="今日新闻、每日新闻、早报、晚报",
)


news_cmd = on_fullmatch(("今日新闻", '早报', '晚报'))


@news_cmd.handle()
async def _():
    url = "http://dwz.2xb.cn/zaob"
    async with httpx.AsyncClient() as client:
        image_url = (await client.get(url)).json().get("imageUrl")
        await news_cmd.finish(await UniMsg.image(url=image_url).export())
