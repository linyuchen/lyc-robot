import asyncio
import logging
from datetime import datetime, timezone, timedelta

import httpx
from nonebot import get_plugin_config, on_fullmatch
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from nonebot_plugin_alconna import UniMsg
from pydantic import BaseModel

from .render import render_status_card

__plugin_meta__ = PluginMetadata(
    name="NewAPI状态",
    description="查看NewAPI服务状态和统计信息",
    usage="ai状态",
)

CST = timezone(timedelta(hours=8))
logger = logging.getLogger("newapi_status")

MAX_RETRIES = 5


class NewApiConfig(BaseModel):
    newapi_base_url: str = ""
    newapi_admin_username: str = ""
    newapi_admin_password: str = ""


config = get_plugin_config(NewApiConfig)


async def _create_authed_client() -> httpx.AsyncClient:
    """Login and return an authenticated client with session cookie + user header."""
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

    # Models — list of strings or list of dicts
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
