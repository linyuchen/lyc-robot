from nonebot import on_fullmatch, get_driver, on_command
from nonebot.internal.adapter.message import Message
from nonebot.message import event_preprocessor
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.exception import IgnoredException
from nonebot_plugin_uninfo import Uninfo

from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="黑名单",
    description="将群或者用户拉入黑名单，不会被机器人响应",
    usage="拉黑群 群号，拉黑用户 用户ID，取消拉黑群 群号，取消拉黑用户 用户ID",
)

from src.plugins.common.permission import check_super_user
from src.plugins.common.rules import rule_args_num
from src.db.model_utils.blacklist import add_black_target, del_black_target, check_black_target, black_user_list, \
    black_group_list

superusers = get_driver().config.superusers

black_list_cmd = on_fullmatch("黑名单", permission=SUPERUSER)
add_black_group_cmd = on_command('拉黑群', force_whitespace=True, permission=SUPERUSER, rule=rule_args_num(num=1))
del_black_group_cmd = on_command('取消拉黑群', force_whitespace=True, permission=SUPERUSER, rule=rule_args_num(1))
add_black_user_cmd = on_command('拉黑用户', force_whitespace=True, permission=SUPERUSER, rule=rule_args_num(1))
del_black_user_cmd = on_command('取消拉黑用户', force_whitespace=True, permission=SUPERUSER, rule=rule_args_num(1))


@black_list_cmd.handle()
async def _():
    res = '黑名单群: ' + '，'.join(black_group_list) + '\n黑名单用户:' + '，'.join(black_user_list)
    await black_list_cmd.finish(res)


@add_black_group_cmd.handle()
async def _(args: Message = CommandArg()):
    group_id = args.extract_plain_text()
    add_black_target('group', group_id)
    await add_black_group_cmd.finish('done')


@add_black_user_cmd.handle()
async def _(args: Message = CommandArg()):
    user_id = args.extract_plain_text()
    add_black_target('user', user_id)
    await add_black_user_cmd.finish('done')


@del_black_group_cmd.handle()
async def _(args: Message = CommandArg()):
    group_id = args.extract_plain_text()
    del_black_target('group', group_id)
    await del_black_group_cmd.finish('done')


@del_black_user_cmd.handle()
async def _(args: Message = CommandArg()):
    user_id = args.extract_plain_text()
    del_black_target('user', user_id)
    await del_black_user_cmd.finish('done')


@event_preprocessor
async def _(session: Uninfo):
    group_id = None
    user_id = session.user.id
    if session.scene.is_group:
        group_id = session.group.id

    if check_super_user(user_id):
        return
    if check_black_target('user', user_id):
        raise IgnoredException(f'ignore black user {user_id}')

    if check_black_target('group', group_id):
        raise IgnoredException(f'ignore black group {group_id}')
