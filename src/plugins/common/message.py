from nonebot import get_bots
from nonebot.adapters.onebot.v11 import Message as OB11Message
from nonebot_plugin_alconna import UniMsg, Image, Target

from src.plugins.common.platforms import get_uni_platform, TYPE_PLATFORM


def get_message_image_urls(message: UniMsg):
    image_urls = []
    try:
        image_msg_segments = message.get(Image)
        image_urls = [image.url for image in image_msg_segments]
    except Exception as e: pass
    if isinstance(message, OB11Message):
        image_msg_segments = message.get('image')
        image_urls = [s.data.get('url') for s in image_msg_segments]
    return image_urls  # + mface_urls
    # mface_msg_segments = message.get('mface')
    # mface_urls = [image.data['url'] for image in mface_msg_segments]


async def uni_send_msg(msg: UniMsg, platform: TYPE_PLATFORM, target: Target):
    bots = get_bots().values()
    for bot in bots:
        if get_uni_platform(bot.adapter.get_name()) == platform:
            await msg.send(target, bot=bot)

async def uni_send_private_msg(msg: UniMsg, user_id: str, platform: TYPE_PLATFORM):
    target = Target(id=user_id, private=True)
    await uni_send_msg(msg, platform, target)



async def uni_send_group_msg(msg: UniMsg, group_id: str, platform: TYPE_PLATFORM ):
    target = Target(id=group_id, private=False)
    await uni_send_msg(msg, platform, target)