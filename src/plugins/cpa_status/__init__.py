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
    name="CPA状态",
    description="查看CLIProxyAPI服务状态和统计信息",
    usage="cpa状态",
)

CST = timezone(timedelta(hours=8))


class CpaConfig(BaseModel):
    cpa_base_url: str = ""
    cpa_management_key: str = ""


config = get_plugin_config(CpaConfig)
logger = logging.getLogger("cpa_status")


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {config.cpa_management_key}"}


MAX_RETRIES = 3


async def _fetch_with_retry(client: httpx.AsyncClient, url: str) -> dict:
    last_err = None
    for i in range(MAX_RETRIES):
        try:
            resp = await client.get(url, headers=_auth_headers(), timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            last_err = e
            if i < MAX_RETRIES - 1:
                await asyncio.sleep(1)
    raise last_err


async def _fetch_usage(client: httpx.AsyncClient) -> dict:
    return await _fetch_with_retry(client, f"{config.cpa_base_url}/v0/management/usage")


async def _fetch_auth_files(client: httpx.AsyncClient) -> list:
    data = await _fetch_with_retry(client, f"{config.cpa_base_url}/v0/management/auth-files")
    return data.get("files", [])


def _build_stats(usage_data: dict, auth_files: list) -> dict:
    usage = usage_data.get("usage", {})

    # Log detailed auth file info
    logger.info("=== CPA Auth Files (%d) ===", len(auth_files))
    for f in auth_files:
        logger.info(
            "  [%s] name=%s provider=%s status=%s status_message=%s "
            "disabled=%s unavailable=%s",
            f.get("id", "?"),
            f.get("name", "?"),
            f.get("provider", "?"),
            f.get("status", "?"),
            f.get("status_message", ""),
            f.get("disabled", False),
            f.get("unavailable", False),
        )

    # Account stats from auth-files
    # transient upstream errors (500/502/503/504) are auto-recoverable, not real errors
    TRANSIENT_MESSAGES = {"transient upstream error", "request failed", "upstream stream closed before first payload"}
    total = len(auth_files)
    active = sum(1 for f in auth_files if f.get("status") == "active" and not f.get("disabled"))
    error = sum(
        1 for f in auth_files
        if f.get("status") == "error" and f.get("status_message", "") not in TRANSIENT_MESSAGES
    )
    transient = sum(
        1 for f in auth_files
        if f.get("status") == "error" and f.get("status_message", "") in TRANSIENT_MESSAGES
    )
    disabled = sum(1 for f in auth_files if f.get("disabled") or f.get("status") == "disabled")

    # Today's date key in CST
    today_key = datetime.now(CST).strftime("%Y-%m-%d")
    requests_by_day = usage.get("requests_by_day") or {}
    tokens_by_day = usage.get("tokens_by_day") or {}
    today_requests = requests_by_day.get(today_key, 0)
    today_tokens = tokens_by_day.get(today_key, 0)

    # Per-model stats aggregated across all APIs
    model_stats: dict[str, dict] = {}
    apis = usage.get("apis") or {}
    for api_info in apis.values():
        models = api_info.get("models") or {}
        for model_name, model_data in models.items():
            if model_name not in model_stats:
                model_stats[model_name] = {"requests": 0, "tokens": 0}
            model_stats[model_name]["requests"] += model_data.get("total_requests", 0)
            model_stats[model_name]["tokens"] += model_data.get("total_tokens", 0)

    # Sort by requests descending, top 8
    top_models = sorted(model_stats.items(), key=lambda x: x[1]["requests"], reverse=True)[:8]

    # Per-provider stats from auth-files
    provider_counts: dict[str, int] = {}
    for f in auth_files:
        p = f.get("provider", "unknown")
        provider_counts[p] = provider_counts.get(p, 0) + 1

    return {
        "total_accounts": total,
        "active_accounts": active,
        "error_accounts": error,
        "transient_accounts": transient,
        "disabled_accounts": disabled,
        "total_requests": usage.get("total_requests", 0),
        "success_count": usage.get("success_count", 0),
        "failure_count": usage.get("failure_count", 0),
        "total_tokens": usage.get("total_tokens", 0),
        "today_requests": today_requests,
        "today_tokens": today_tokens,
        "top_models": top_models,
        "provider_counts": provider_counts,
        "updated_at": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S"),
    }


cpa_status_cmd = on_fullmatch("cpa状态")


@cpa_status_cmd.handle()
async def _():
    if not config.cpa_base_url:
        await cpa_status_cmd.finish("未配置 CPA_BASE_URL")

    try:
        async with httpx.AsyncClient() as client:
            usage_data, auth_files = await asyncio.gather(
                _fetch_usage(client),
                _fetch_auth_files(client),
            )
        stats = _build_stats(usage_data, auth_files)
    except httpx.HTTPStatusError as e:
        await cpa_status_cmd.finish(f"API请求失败: HTTP {e.response.status_code}")
    except Exception as e:
        await cpa_status_cmd.finish(f"获取状态失败: {e}")

    image_bytes = render_status_card(stats)
    await cpa_status_cmd.finish(await UniMsg.image(raw=image_bytes).export())
