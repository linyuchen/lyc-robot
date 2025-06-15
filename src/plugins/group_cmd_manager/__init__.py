from nonebot import on_fullmatch, on_command, get_driver, Bot
from nonebot.internal.adapter import Event
from nonebot.internal.matcher import Matcher
from nonebot.params import CommandArg, Message
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from nonebot_plugin_uninfo import Uninfo

from src.db.model_utils.group_cmd_manager import check_group_message, get_group_ignore_cmds, add_group_ignore_cmd, remove_group_ignore_cmd

__plugin_meta__ = PluginMetadata(
    name="群命令屏蔽",
    description="群里设置屏蔽某些命令",
    usage="屏蔽命令列表、添加屏蔽命令 命令名、删除屏蔽命令 命令名",
)

from ..common.rules import rule_is_group_msg, inject_plugin_rule

driver = get_driver()


def check_group_cmd_permission(matcher: Matcher, bot: Bot, event: Event):
    message = getattr(event, 'message', None)
    if not message:
        return True
    msg_text = ''
    if isinstance(message, Message):
        msg_text = message.extract_plain_text().strip()
    elif isinstance(message, list):
        msg_text = ''
        for msg in message:
            msg_text = msg.get('text', '').strip()
    not_ignore = check_group_message(vars(event).get('group_id'), msg_text)
    return not_ignore


@driver.on_startup
async def _():
    inject_plugin_rule(check_group_cmd_permission)


list_cmd = on_fullmatch("屏蔽命令列表", permission=SUPERUSER, rule=rule_is_group_msg())


@list_cmd.handle()
async def _(session: Uninfo):
    group_id = str(session.group.id)
    res = '屏蔽命令列表：' + '，'.join(get_group_ignore_cmds(group_id))
    await list_cmd.finish(res)


add_cmd = on_command("添加屏蔽命令", permission=SUPERUSER, rule=rule_is_group_msg())


@add_cmd.handle()
async def _(session: Uninfo, args: Message = CommandArg()):
    group_id = session.group.id
    cmd = args.extract_plain_text()
    add_group_ignore_cmd(str(group_id), cmd)
    await add_cmd.finish('done')


del_cmd = on_command("删除屏蔽命令", permission=SUPERUSER, rule=rule_is_group_msg())


@del_cmd.handle()
async def _(session: Uninfo, args: Message = CommandArg()):
    group_id = session.group.id
    cmd = args.extract_plain_text()
    remove_group_ignore_cmd(str(group_id), cmd)
    await del_cmd.finish('done')
