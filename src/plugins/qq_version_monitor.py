from nonebot import require, get_driver
from nonebot.internal.adapter import Message
from nonebot.params import CommandArg
from nonebot.plugin.on import on_command

from src.plugins.common.message import uni_send_group_msg

require("nonebot_plugin_apscheduler")

from nonebot_plugin_apscheduler import scheduler

from nonebot import on_fullmatch
from nonebot.plugin import PluginMetadata
from nonebot_plugin_alconna import UniMsg
from nonebot_plugin_waiter import waiter

from src.common.qq_version_monitor import qqnt_version_monitor
from src.db.model_utils.qq_version_monitor import get_versions, add_subscriber, remove_subscriber, get_subscribers, \
    save_version, get_version

__plugin_meta__ = PluginMetadata(
    name="QQ版本监控",
    description="可订阅QQ版本更新，查询历史版本",
    usage="订阅QQ更新、QQ历史版本, QQ版本 <版本号>"
)

driver = get_driver()

from src.plugins.common.depends import Group


async def get_qqnt_new_version():
    version, detail = await qqnt_version_monitor.get_new_version()
    if version:
        save_version(version, detail)
    return version, detail

@scheduler.scheduled_job("cron", minute="*/30", id="qqnt_version_monitor")
async def qqnt_version_scheduler():
    version, detail = await get_qqnt_new_version()
    if not version:
        return
    save_version(version, detail)
    subscriber_list = get_subscribers()
    msg = UniMsg.text(detail)
    for subscriber in subscriber_list:
        await uni_send_group_msg(msg, subscriber.group_id, subscriber.platform)


@driver.on_startup
async def _():
    await get_qqnt_new_version()


qqnt_versions_cmd = on_fullmatch(('QQ版本列表', 'qq版本列表', 'QQ历史版本', 'qq历史版本'))
subscribe_qqnt_new_version_cmd = on_fullmatch(('订阅QQ更新', '订阅qq更新'))
unsubscribe_qqnt_new_version_cmd = on_fullmatch(('取消订阅QQ更新', '取消订阅qq更新'))
qqnt_search_cmd = on_command('qq版本', aliases={'QQ版本'})


@qqnt_versions_cmd.handle()
async def _():
    versions = get_versions()
    if not versions:
        await qqnt_versions_cmd.finish("暂无QQ版本信息")

    text = "已记录的QQ版本列表:\n"
    for index, version in enumerate(versions):
        text += f"{index}: {version.version}\n"

    TIMEOUT = 20
    text += f'\n\n{TIMEOUT}秒内回复序号获取版本详情'
    await qqnt_versions_cmd.send(text)

    @waiter(waits=["message"], keep_session=True)
    async def check(msg: UniMsg):
        return msg.extract_plain_text()

    async for resp in check(timeout=TIMEOUT):
        if not resp or not resp.isdigit():
            continue
        index = int(resp)
        if index < 0 or index >= len(versions):
            continue
        version = versions[index]
        await qqnt_versions_cmd.send(version.detail)

    qqnt_versions_cmd.finish()


@subscribe_qqnt_new_version_cmd.handle()
async def _(group: Group):
    if not group:
        return await subscribe_qqnt_new_version_cmd.finish("请在群聊中使用此命令")
    add_subscriber(group.platform, group.group_id)
    await subscribe_qqnt_new_version_cmd.finish("已订阅QQ新版本更新，若有新版本会在群里通知")


@unsubscribe_qqnt_new_version_cmd.handle()
async def _(group: Group):
    if not group:
        return await unsubscribe_qqnt_new_version_cmd.finish("请在群聊中使用此命令")
    remove_subscriber(group.platform, group.group_id)
    await unsubscribe_qqnt_new_version_cmd.finish("已取消订阅QQ新版本更新")


@qqnt_search_cmd.handle()
async def _(args: Message = CommandArg()):
    version = args.extract_plain_text()
    version = version.strip()
    version_info = get_version(version)
    if version_info:
        await qqnt_search_cmd.finish(version_info.detail)
    else:
        await qqnt_search_cmd.finish(f'数据库没有找到QQ{version}')

