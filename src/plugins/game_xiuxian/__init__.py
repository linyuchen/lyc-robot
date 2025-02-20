import random
import time

from nonebot import on_fullmatch, on_command
from nonebot.plugin import PluginMetadata
from nonebot_plugin_uninfo import Uninfo

__plugin_meta__ = PluginMetadata(
    name="修仙游戏",
    description="简单的挂机修仙小游戏",
    usage="修仙面板、修仙签到、闭关、出关、修仙榜",
)

from src.db.model_utils.game_xiuxian import sign, save_user, get_top
from src.db.models.game_xiuxian import SECLUSION_SECOND_LEVEL_POINT
from src.plugins.game_xiuxian.depends import GameUser

cmd_panel = on_fullmatch('修仙面板')
cmd_sign = on_fullmatch('修仙签到')
cmd_seclusion = on_fullmatch('闭关')
cmd_exit_seclusion = on_fullmatch('出关')
cmd_top = on_command('修仙榜', aliases={'修仙排名', '修仙排行', '修仙排行榜', '天骄榜'})


@cmd_sign.handle()
async def _(session: Uninfo, game_user: GameUser):
    group_id = session.group.id if session.scene.is_group else None
    if sign(session.user.id, session.adapter.value, group_id, session.user.name):
        add_point = random.randint(100, 1000)
        game_user.point += add_point
        save_user(game_user)
        await cmd_sign.finish(f'【{session.user.name}】签到成功，获得 {add_point} 灵力')
    else:
        await cmd_sign.finish(f'【{session.user.name}】今天已经签到过了')


@cmd_panel.handle()
async def _(session: Uninfo, game_user: GameUser):
    resp = f'道友：{session.user.name}\n'
    resp += f'境界：{game_user.level_name}\n'
    resp += f'灵力: {game_user.point} / {game_user.next_level_point}\n'
    if game_user.is_seclusion:
        resp += '当前状态：闭关中'
    else:
        resp += '当前状态：空闲中'
    await cmd_panel.finish(resp)


@cmd_seclusion.handle()
async def _(session: Uninfo, game_user: GameUser):
    if not game_user.is_seclusion:
        game_user.is_seclusion = True
        game_user.seclusion_timestamp = time.time()
        save_user(game_user)
    resp = f'当前每秒闭关获得灵力：{SECLUSION_SECOND_LEVEL_POINT * (game_user.level + 1)}'
    await cmd_seclusion.finish(f'【{session.user.name}】已经闭关了\n{resp}')


@cmd_exit_seclusion.handle()
async def _(session: Uninfo, game_user: GameUser):
    if game_user.is_seclusion:
        game_user.is_seclusion = False
        seclusion_total_seconds = time.time() - game_user.seclusion_timestamp
        point = seclusion_total_seconds * (game_user.level + 1) * SECLUSION_SECOND_LEVEL_POINT
        point = int(point)
        game_user.point += point
        save_user(game_user)
        await cmd_exit_seclusion.finish(f'【{session.user.name}】出关，获得 {point} 灵力')
    else:
        await cmd_exit_seclusion.finish(f'【{session.user.name}】还未闭关')


@cmd_top.handle()
async def _(session: Uninfo):
    group_id = session.group.id if session.scene.is_group else None
    top_users = get_top(group_id, session.adapter.value)
    resp = f''
    for index, user in enumerate(top_users):
        resp += f'{index +1}. {user.username}(灵力: {user.point})\n'

    await cmd_top.finish(resp)