import asyncio
import random
from dataclasses import dataclass, field

from nonebot import on_command, on_notice, Bot
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.params import CommandArg, Event, Message
from nonebot.plugin import PluginMetadata
from nonebot_plugin_uninfo import Uninfo

from nonebot.permission import Permission
from src.plugins.common.permission import check_group_admin
from src.plugins.common.rules import rule_args_num, rule_is_group_msg

__plugin_meta__ = PluginMetadata(
    name="抽奖",
    description="发起群抽奖，群成员贴表情参与，到时间自动开奖",
    usage="抽奖 <人数> <抽奖说明>，如：抽奖 2 抽3个ChatGPT Team名额",
)

LOTTERY_DURATION = 5*60 # 秒


@dataclass
class LotteryInfo:
    group_id: int
    message_id: int
    user_id: int
    winner_count: int
    description: str
    participants: set[int] = field(default_factory=set)
    task: asyncio.Task | None = None


# 每个群同时只能有一个抽奖
active_lotteries: dict[int, LotteryInfo] = {}


# ========== 发起抽奖 ==========

lottery_cmd = on_command("抽奖", rule=rule_args_num(min_num=2) & rule_is_group_msg(), permission=Permission(check_group_admin))


@lottery_cmd.handle()
async def _(bot: Bot, event: Event, session: Uninfo, args: Message = CommandArg()):
    group_id = int(session.group.id)
    user_id = int(session.user.id)

    if group_id in active_lotteries:
        await lottery_cmd.finish("当前群已有进行中的抽奖，请等待开奖后再发起新的抽奖")

    text = args.extract_plain_text().strip()
    parts = text.split(maxsplit=1)
    try:
        winner_count = int(parts[0])
    except ValueError:
        await lottery_cmd.finish("人数必须是数字，如：抽奖 2 抽3个ChatGPT Team名额")
    if winner_count < 1:
        await lottery_cmd.finish("中奖人数至少为1")

    description = parts[1]

    minutes = LOTTERY_DURATION // 60
    announce_text = (
        f"🎉 抽奖开始！\n"
        f"📌 {description}\n"
        f"🏆 中奖人数：{winner_count}\n"
        f"⏰ 开奖时间：{minutes}分钟后\n\n"
        f"👉 在本消息贴上任意表情即可参与"
    )

    rsp = await bot.send(event, announce_text)
    message_id = rsp["message_id"]

    # bot自己先贴一个表情（爱心 emoji_id=66）作为示范
    await bot.call_api("set_msg_emoji_like", message_id=message_id, emoji_id="66")

    lottery = LotteryInfo(
        group_id=group_id,
        message_id=message_id,
        user_id=user_id,
        winner_count=winner_count,
        description=description,
    )
    active_lotteries[group_id] = lottery

    lottery.task = asyncio.create_task(draw_lottery(bot, group_id))


# ========== 收集贴表情参与者 ==========

emoji_like_handler = on_notice()


@emoji_like_handler.handle()
async def _(event: Event):
    raw = event.dict()
    if raw.get("notice_type") != "group_msg_emoji_like":
        return
    if not raw.get("is_add"):
        return

    group_id = raw.get("group_id")
    message_id = raw.get("message_id")
    user_id = raw.get("user_id")

    lottery = active_lotteries.get(group_id)
    if not lottery:
        return
    if message_id != lottery.message_id:
        return

    lottery.participants.add(user_id)


# ========== 定时开奖 ==========

async def draw_lottery(bot: Bot, group_id: int):
    await asyncio.sleep(LOTTERY_DURATION)

    lottery = active_lotteries.pop(group_id, None)
    if not lottery:
        return

    # 去掉bot自身
    participants = list(lottery.participants - {int(bot.self_id)})

    if not participants:
        await bot.send_group_msg(
            group_id=group_id,
            message="⏰ 抽奖已结束\n\n无人参与，本次抽奖流拍~",
        )
        return

    winner_count = min(lottery.winner_count, len(participants))
    winners = random.sample(participants, winner_count)

    # 获取中奖者昵称
    winner_lines = []
    at_segments = MessageSegment.text("")
    for uid in winners:
        try:
            info = await bot.get_group_member_info(group_id=group_id, user_id=uid)
            nick = info.get("card") or info.get("nickname") or str(uid)
        except Exception:
            nick = str(uid)
        winner_lines.append(f"🎊 {nick}（{uid}）")
        at_segments += MessageSegment.at(uid)

    result_text = (
        f"⏰ 抽奖结束！\n"
        f"📌 {lottery.description}\n"
        f"👥 参与人数：{len(participants)}\n"
        f"🏆 中奖名单：\n" + "\n".join(winner_lines)
    )

    await bot.send_group_msg(
        group_id=group_id,
        message=at_segments + MessageSegment.text(f"\n\n{result_text}"),
    )
