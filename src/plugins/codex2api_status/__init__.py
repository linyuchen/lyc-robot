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
    name="Codex2API状态",
    description="查看Codex2API服务状态和统计信息",
    usage="codex2api状态",
)

CST = timezone(timedelta(hours=8))
logger = logging.getLogger("codex2api_status")

MAX_RETRIES = 3


class Codex2ApiConfig(BaseModel):
    codex2api_base_url: str = ""
    codex2api_admin_key: str = ""


config = get_plugin_config(Codex2ApiConfig)


def _headers() -> dict:
    return {"X-Admin-Key": config.codex2api_admin_key}


async def _fetch(client: httpx.AsyncClient, path: str) -> dict:
    url = f"{config.codex2api_base_url}/api/admin{path}"
    last_err = None
    for i in range(MAX_RETRIES):
        try:
            resp = await client.get(url, headers=_headers(), timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            last_err = e
            if i < MAX_RETRIES - 1:
                await asyncio.sleep(1)
    raise last_err


def _build_stats(ops: dict, accounts: list) -> dict:
    # Log account details
    logger.info("=== Codex2API Accounts (%d) ===", len(accounts))
    for a in accounts:
        logger.info(
            "  [%s] name=%s email=%s status=%s plan=%s health=%s locked=%s",
            a.get("id", "?"), a.get("name", "?"), a.get("email", "?"),
            a.get("status", "?"), a.get("plan_type", "?"),
            a.get("health_tier", "?"), a.get("locked", False),
        )

    # Account status breakdown — dynamic keyword classification
    KEYWORD_CATEGORIES = [
        ("unauthorized", "账号失效"),
        ("rate_limited", "频率限制"),
        ("usage_exhausted", "额度耗尽"),
        ("cooldown", "冷却中"),
    ]

    def _classify(status: str) -> str:
        s = status.lower()
        for keyword, category in KEYWORD_CATEGORIES:
            if keyword in s:
                return category
        if s == "active":
            return "active"
        if s == "error":
            return "账号异常"
        return "账号无效"

    total = len(accounts)
    active = 0
    locked = 0
    status_breakdown: dict[str, int] = {}
    for a in accounts:
        if a.get("locked"):
            locked += 1
            continue
        cat = _classify(a.get("status", ""))
        if cat == "active":
            active += 1
        else:
            status_breakdown[cat] = status_breakdown.get(cat, 0) + 1

    # Traffic from ops overview
    traffic = ops.get("traffic", {})
    runtime = ops.get("runtime", {})
    requests = ops.get("requests", {})

    return {
        "total_accounts": total,
        "active_accounts": active,
        "error_accounts": sum(status_breakdown.values()),
        "locked_accounts": locked,
        "status_breakdown": status_breakdown,
        "today_requests": traffic.get("today_requests", 0),
        "today_tokens": traffic.get("today_tokens", 0),
        "qps": traffic.get("qps", 0),
        "rpm": traffic.get("rpm", 0),
        "tpm": traffic.get("tpm", 0),
        "error_rate": traffic.get("error_rate", 0),
        "active_requests": requests.get("active", 0),
        "total_runtime_requests": requests.get("total", 0),
        "uptime": ops.get("uptime_seconds"),
        "goroutines": runtime.get("goroutines", 0),
        "updated_at": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S"),
    }


codex_status_cmd = on_fullmatch("codex2api状态")


@codex_status_cmd.handle()
async def _():
    if not config.codex2api_base_url:
        await codex_status_cmd.finish("未配置 CODEX2API_BASE_URL")

    try:
        async with httpx.AsyncClient() as client:
            ops, accounts_resp = await asyncio.gather(
                _fetch(client, "/ops/overview"),
                _fetch(client, "/accounts"),
            )
        accounts = accounts_resp if isinstance(accounts_resp, list) else accounts_resp.get("accounts", [])
        stats = _build_stats(ops, accounts)
    except httpx.HTTPStatusError as e:
        await codex_status_cmd.finish(f"API请求失败: HTTP {e.response.status_code}")
    except Exception as e:
        await codex_status_cmd.finish(f"获取状态失败: {e}")

    image_bytes = render_status_card(stats)
    await codex_status_cmd.finish(await UniMsg.image(raw=image_bytes).export())
