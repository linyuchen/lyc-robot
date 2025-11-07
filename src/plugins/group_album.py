from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.internal.adapter import Message
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from nonebot_plugin_alconna import UniMsg

__plugin_meta__ = PluginMetadata(
    name="相册",
    description="群相册功能，对着图片引用发送 相册 相册名",
    usage="相册 相册1",
)

group_album_cmd = on_command('相册')


@group_album_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, params: Message = CommandArg()):
    if not params:
        return
        return await group_album_cmd.finish('请指定相册名，如 相册 相册名')
    if not event.reply:
        return
        return await group_album_cmd.finish('请对图片引用发送此命令')
    album_name = params.extract_plain_text().strip()
    album_id = ''
    group_album_list = await bot.call_api('get_group_album_list', group_id=event.group_id)
    for album in group_album_list:
        if album['name'] == album_name:
            album_id = album['album_id']
            break
    if not album_id:
        create_result = await bot.call_api('create_group_album', group_id=event.group_id, name=album_name)
        album_id = create_result['album_id']
    img_urls = []
    for reply_msg in event.reply.message:
        if reply_msg.type in ['image', 'mface']:
            img_url = reply_msg.data.get('url')
            img_urls.append(img_url)
    if img_urls:
        await bot.call_api('upload_group_album', group_id=event.group_id, album_id=album_id, files=img_urls)
