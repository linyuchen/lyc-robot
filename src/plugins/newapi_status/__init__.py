import asyncio
import logging
from datetime import datetime, timezone, timedelta

import httpx
from nonebot import get_plugin_config, on_fullmatch, on_command, require
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from nonebot_plugin_alconna import UniMsg
from nonebot_plugin_uninfo import Uninfo
from pydantic import BaseModel

from src.db.model_utils.newapi_model_monitor import (
    add_monitor, remove_monitor, get_all_monitors, get_monitors_by_target, update_status,
)
from src.plugins.common.message import uni_send_group_msg, uni_send_private_msg
from src.plugins.common.platforms import get_uni_platform

from .render import render_status_card

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler  # noqa: E402

__plugin_meta__ = PluginMetadata(
    name="NewAPI状态",
    description="查看NewAPI服务状态和统计信息",
    usage="ai状态 / 监控模型 <名称> / 取消监控 <名称> / 监控列表",
)

CST = timezone(timedelta(hours=8))
logger = logging.getLogger("newapi_status")

MAX_RETRIES = 5


class NewApiConfig(BaseModel):
    newapi_base_url: str = ""
    newapi_admin_username: str = ""
    newapi_admin_password: str = ""


config = get_plugin_config(NewApiConfig)


# ── API helpers ──────────────────────────────────────

async def _create_authed_client() -> httpx.AsyncClient:
    last_err = None
    for i in range(MAX_RETRIES):
        client = httpx.AsyncClient(follow_redirects=True, timeout=15)
        try:
            resp = await client.post(
                f"{config.newapi_base_url}/api/user/login",
                json={"username": config.newapi_admin_username, "password": config.newapi_admin_password},
            )
            resp.raise_for_status()
            body = resp.json()
            if not body.get("success"):
                raise Exception(body.get("message", "login failed"))
            user_id = body["data"]["id"]
            client.headers["New-API-User"] = str(user_id)
            return client
        except Exception as e:
            await client.aclose()
            last_err = e
            if i < MAX_RETRIES - 1:
                await asyncio.sleep(2)
    raise last_err


async def _get(client: httpx.AsyncClient, path: str, params: dict = None) -> dict:
    for i in range(MAX_RETRIES):
        try:
            resp = await client.get(f"{config.newapi_base_url}{path}", params=params)
            if resp.status_code == 429 and i < MAX_RETRIES - 1:
                await asyncio.sleep(5)
                continue
            resp.raise_for_status()
            body = resp.json()
            if not body.get("success", True):
                raise Exception(body.get("message", "request failed"))
            return body
        except Exception:
            if i < MAX_RETRIES - 1:
                await asyncio.sleep(2)
            else:
                raise


async def _fetch_enabled_models() -> list[str]:
    client = await _create_authed_client()
    try:
        body = await _get(client, "/api/channel/models_enabled/")
    finally:
        await client.aclose()
    data = (body or {}).get("data") or []
    if isinstance(data, list) and data and isinstance(data[0], str):
        return data
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return [m.get("id", "") for m in data if m.get("id")]
    return []


# ── Status card ──────────────────────────────────────

def _build_stats(channels_body: dict, log_stat_today: dict, log_stat_total: dict, models_body: dict) -> dict:
    channels = (channels_body or {}).get("data") or channels_body
    if isinstance(channels, dict):
        channels = channels.get("items") or channels.get("data") or []
    if not isinstance(channels, list):
        channels = []

    total = len(channels)
    enabled = sum(1 for c in channels if c.get("status") == 1)
    disabled = total - enabled

    today = (log_stat_today or {}).get("data") or {}
    total_stat = (log_stat_total or {}).get("data") or {}

    models_data = (models_body or {}).get("data") or []
    if isinstance(models_data, list) and models_data:
        if isinstance(models_data[0], str):
            model_names = sorted(models_data)
        elif isinstance(models_data[0], dict):
            model_names = sorted(set(m.get("id", "") for m in models_data if m.get("id")))
        else:
            model_names = []
    else:
        model_names = []

    return {
        "total_channels": total,
        "enabled_channels": enabled,
        "disabled_channels": disabled,
        "today_quota": today.get("quota", 0),
        "today_rpm": today.get("rpm", 0),
        "today_tpm": today.get("tpm", 0),
        "total_quota": total_stat.get("quota", 0),
        "models": model_names,
        "updated_at": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S"),
    }


newapi_status_cmd = on_fullmatch(("ai状态", "AI状态"))


@newapi_status_cmd.handle()
async def _():
    if not config.newapi_base_url:
        await newapi_status_cmd.finish("未配置 NEWAPI_BASE_URL")

    try:
        client = await _create_authed_client()
        try:
            now = datetime.now(CST)
            today_start = int(datetime(now.year, now.month, now.day, tzinfo=CST).timestamp())
            channels_body = await _get(client, "/api/channel/", {"page": 1, "page_size": 1000})
            log_stat_today = await _get(client, "/api/log/stat/", {"start_timestamp": today_start})
            log_stat_total = await _get(client, "/api/log/stat/")
            models_body = await _get(client, "/api/channel/models_enabled/")
        finally:
            await client.aclose()
        stats = _build_stats(channels_body, log_stat_today, log_stat_total, models_body)
    except httpx.HTTPStatusError as e:
        await newapi_status_cmd.finish(f"API请求失败: HTTP {e.response.status_code}")
    except Exception as e:
        await newapi_status_cmd.finish(f"获取状态失败: {e}")

    image_bytes = render_status_card(stats)
    await newapi_status_cmd.finish(await UniMsg.image(raw=image_bytes).export())


# ── Model monitoring ─────────────────────────────────

monitor_add_cmd = on_command("监控模型")
monitor_remove_cmd = on_command("取消模型监控")
monitor_list_cmd = on_fullmatch("监控模型列表")


@monitor_add_cmd.handle()
async def _(session: Uninfo, args=CommandArg()):
    model_name = args.extract_plain_text().strip()
    if not model_name:
        await monitor_add_cmd.finish("用法: 监控模型 <模型名称>")

    platform = get_uni_platform(session.adapter.value)
    is_private = not session.scene.is_group
    target_id = session.group.id if session.scene.is_group else session.user.id

    ok = add_monitor(model_name, target_id, platform, is_private)
    if ok:
        await monitor_add_cmd.finish(f"已添加监控: {model_name}")
    else:
        await monitor_add_cmd.finish(f"已在监控中: {model_name}")


@monitor_remove_cmd.handle()
async def _(session: Uninfo, args=CommandArg()):
    model_name = args.extract_plain_text().strip()
    if not model_name:
        await monitor_remove_cmd.finish("用法: 取消模型监控 <模型名称>")

    platform = get_uni_platform(session.adapter.value)
    target_id = session.group.id if session.scene.is_group else session.user.id

    ok = remove_monitor(model_name, target_id, platform)
    if ok:
        await monitor_remove_cmd.finish(f"已取消监控: {model_name}")
    else:
        await monitor_remove_cmd.finish(f"未找到监控: {model_name}")


@monitor_list_cmd.handle()
async def _(session: Uninfo):
    platform = get_uni_platform(session.adapter.value)
    target_id = session.group.id if session.scene.is_group else session.user.id

    monitors = get_monitors_by_target(target_id, platform)
    if not monitors:
        await monitor_list_cmd.finish("当前会话没有监控任何模型")

    lines = [f"当前监控 ({len(monitors)} 个):"]
    for m in monitors:
        status = "✓可用" if m.last_status else ("✗不可用" if m.last_status is False else "?未知")
        lines.append(f"  {m.model_name} [{status}]")
    await monitor_list_cmd.finish("\n".join(lines))


# ── Scheduled check (every 5 minutes) ───────────────

@scheduler.scheduled_job("cron", minute="*/5", id="model_monitor_check")
async def model_monitor_check():
    if not config.newapi_base_url:
        return

    monitors = get_all_monitors()
    if not monitors:
        return

    try:
        enabled_models = await _fetch_enabled_models()
    except Exception as e:
        logger.warning("Model monitor fetch failed: %s", e)
        return

    enabled_set = set(enabled_models)

    for monitor in monitors:
        is_available = monitor.model_name in enabled_set
        if monitor.last_status is None:
            update_status(monitor.id, is_available)
            continue
        if is_available != monitor.last_status:
            update_status(monitor.id, is_available)
            status_text = "已可用 ✓" if is_available else "已不可用 ✗"
            msg = UniMsg.text(f"[模型监控] {monitor.model_name} {status_text}")
            try:
                if monitor.is_private:
                    await uni_send_private_msg(msg, monitor.target_id, monitor.platform)
                else:
                    await uni_send_group_msg(msg, monitor.target_id, monitor.platform)
            except Exception as e:
                logger.warning("Failed to send monitor notification: %s", e)

