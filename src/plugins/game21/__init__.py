import asyncio
import threading

from nonebot import on_command, Bot, on_fullmatch
from nonebot.params import CommandArg, Event, Message
from nonebot.plugin import PluginMetadata
from nonebot_plugin_uninfo import Uninfo

__plugin_meta__ = PluginMetadata(
    name="21点",
    description="21点棋牌游戏",
    usage="21点 下注数量，如21点 100",
)

from src.common.game21.game21point import Game
from src.common.group_point.action import group_point_action
from src.plugins.common.rules import rule_args_num


class Game21(Game):

    def __init__(self):
        super().__init__()
        self.currency = group_point_action.POINT_NAME

    def add_point(self, group_qq, qq, point):
        return group_point_action.add_point(group_qq, qq, point)

    def get_point(self, group_qq, qq):
        return group_point_action.get_member(group_qq, qq).point


group_instances = {}


def get_game_instance(group_qq: str):
    if group_qq in group_instances:
        return group_instances[group_qq]
    game = Game21()
    group_instances[group_qq] = game
    return game


game21_cmd = on_command("21点",  rule=rule_args_num(max_num=1))


@game21_cmd.handle()
async def _(bot: Bot, event: Event, session: Uninfo, args: Message = CommandArg()):
    if not session.scene.is_group:
        return
    group_id = str(session.group.id)
    user_id = str(session.user.id)
    user_nick = session.user.nick
    game = get_game_instance(group_id)
    if not args.extract_plain_text():
        point = 100
    else:
        try:
            point = int(args.extract_plain_text())
        except Exception as e:
            return

    def reply(text):
        threading.Thread(target=lambda: asyncio.run(bot.send(event, text)), daemon=True).start()

    start_result = game.start_game(group_id, user_id, user_nick,
                                   str(point), reply)

    start_result += "\n\n发送“21点换牌”可以换牌，换牌需要下注的十分之一费用\n"
    await game21_cmd.finish(start_result)


game21_update_cmd = on_fullmatch("21点换牌")


@game21_update_cmd.handle()
async def _(session: Uninfo):
    if not session.scene.is_group:
        return
    group_id = session.group.id
    user_id = session.user.id
    user_nick = session.user.nick
    res = get_game_instance(str(group_id)).update_poker_list(str(group_id), str(user_id),
                                                                   user_nick)
    await game21_update_cmd.finish(res)
