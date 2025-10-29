import tempfile
from pathlib import Path

import httpx
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent

from src.common.utils.nsfw_detector.image_detector import nsfw_detect

__plugin_meta__ = PluginMetadata(
    name="涩图撤回",
    description="检测到涩图后撤回消息，只支持QQ平台，需要管理员权限",
    usage="",
)


group_admin_state = {}

async def _(bot: Bot, event: GroupMessageEvent):
    group_id = event.group_id
    is_admin = group_admin_state.get(group_id)
    if is_admin is None:
        member_info = await bot.get_group_member_info(group_id=group_id, user_id=int(bot.self_id))
        member_info_role = member_info.get('role')
        is_admin = member_info_role in ['admin', 'owner']
        group_admin_state[group_id] = is_admin
    if not is_admin:
        return
    for msg in event.message:
        if msg.type == 'image':
            img_url = msg.data.get('url')
            tmp_path = Path(tempfile.mktemp(suffix='.jpg'))
            img_bytes = (await httpx.AsyncClient().get(url=img_url)).content
            tmp_path.write_bytes(img_bytes)
            is_nsfw = nsfw_detect(tmp_path)
            tmp_path.unlink()
            if is_nsfw:
                await bot.delete_msg(message_id=event.message_id)