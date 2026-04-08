import asyncio
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


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {config.cpa_management_key}"}


async def _fetch_usage(client: httpx.AsyncClient) -> dict:
    resp = await client.get(
        f"{config.cpa_base_url}/v0/management/usage",
        headers=_auth_headers(),
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


async def _fetch_auth_files(client: httpx.AsyncClient) -> list:
    resp = await client.get(
        f"{config.cpa_base_url}/v0/management/auth-files",
        headers=_auth_headers(),
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("files", [])


def _build_stats(usage_data: dict, auth_files: list) -> dict:
    usage = usage_data.get("usage", {})

    # Account stats from auth-files
    total = len(auth_files)
    active = sum(1 for f in auth_files if f.get("status") == "active" and not f.get("disabled"))
    error = sum(1 for f in auth_files if f.get("status") == "error")
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
