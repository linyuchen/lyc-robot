from nonebot import on_command
from nonebot.params import Message, CommandArg
from nonebot_plugin_uninfo import Uninfo

from src.plugins.common.permission import check_group_admin
from src.plugins.common.rules import rule_is_group_msg
from src.db.model_utils.github import add_subscriber_to_db

add_subscriber_cmd = on_command('subscribe', permission=check_group_admin, rule=rule_is_group_msg())

@add_subscriber_cmd.handle()
async def handle_add_subscriber(info: Uninfo, args: Message = CommandArg()):
    adapter_name = info.adapter.value
    group_id = info.group.id
    args = args.extract_plain_text().split()
    owner_repo = args[0]
    owner_repo = owner_repo.split('/')
    if len(owner_repo) != 2:
        await info.finish("参数错误, 请检查owner/repo event/action格式, 示例: /subscribe owner/repo star/created")
        return
    owner, repo = owner_repo
    event_action = ''
    if len(args) > 1:
        event_action = args[1]
    event_action = event_action.split('/')
    event = event_action[0]
    action = ''
    if len(event_action) >= 2:
        action = event_action[1]

    add_subscriber_to_db(group_id, adapter_name, owner, repo, event, action)
    await info.finish("订阅成功")
