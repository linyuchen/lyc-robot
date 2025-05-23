from nonebot.adapters.onebot.v11 import Message as OB11Message
from nonebot_plugin_alconna import UniMsg, Image


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
