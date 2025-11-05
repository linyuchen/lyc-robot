import json

from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageEvent, PrivateMessageEvent
from nonebot.plugin import PluginMetadata
from nonebot.plugin.on import on_fullmatch

__plugin_meta__ = PluginMetadata(
    name="消息调式",
    description="查看消息结构工具",
    usage="对着消息回复 取",
)

get_msg_cmd = on_fullmatch('取')


@get_msg_cmd.handle()
async def get_msg(bot: Bot, event: MessageEvent):
    if not event.reply:
        return
    onebot11_msg = event.reply.model_dump()
    onebot11_msg.pop('raw')
    forward_data = {
        'messages': [
            {
                'type': 'node',
                'data': {
                    'uin': 10000,
                    'name': 'NT',
                    'content': {
                        'type': 'text',
                        'data': {
                            'text': json.dumps(event.reply.raw, indent=2, ensure_ascii=False)
                        }
                    }
                }
            },
            {
                'type': 'node',
                'data': {
                    'uin': 10000,
                    'name': 'OneBot11',
                    'content': {
                        'type': 'text',
                        'data': {
                            'text': json.dumps(onebot11_msg, indent=2, ensure_ascii=False)
                        }
                    }
                }
            }
        ]
    }
    if isinstance(event, GroupMessageEvent):
        forward_data['group_id'] = event.group_id
        await bot.call_api('send_group_forward_msg', **forward_data)
    elif isinstance(event, PrivateMessageEvent):
        forward_data['user_id'] = event.user_id
        await bot.call_api('send_private_forward_msg', **forward_data)

