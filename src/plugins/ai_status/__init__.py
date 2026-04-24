import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta

import httpx
from nonebot import get_plugin_config, on_fullmatch
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from nonebot_plugin_alconna import UniMsg
from pydantic import BaseModel

from .render import render_status_card

__plugin_meta__ = PluginMetadata(
    name="AI状态",
    description="查看所有AI服务的综合状态",
    usage="AI状态",
)

CST = timezone(timedelta(hours=8))
logger = logging.getLogger("ai_status")

MAX_RETRIES = 5


class AIStatusConfig(BaseModel):
    sub2api_base_url: str = ""
    sub2api_admin_email: str = ""
    sub2api_admin_password: str = ""
    cpa_base_url: str = ""
    cpa_management_key: str = ""
    codex2api_base_url: str = ""
    codex2api_admin_key: str = ""


config = get_plugin_config(AIStatusConfig)

# Sub2API JWT cache
_jwt_token: str | None = None
_jwt_expires_at: float = 0


async def _retry(coro_factory, retries=MAX_RETRIES):
    last_err = None
    for i in range(retries):
        try:
            return await coro_factory()
        except Exception as e:
            last_err = e
            if i < retries - 1:
                await asyncio.sleep(1)
    raise last_err


# ── Sub2API ──────────────────────────────────────────

async def _sub2api_login(client: httpx.AsyncClient) -> str:
    global _jwt_token, _jwt_expires_at
    if _jwt_token and time.time() < _jwt_expires_at - 60:
        return _jwt_token

    resp = await client.post(
        f"{config.sub2api_base_url}/api/v1/auth/login",
        json={"email": config.sub2api_admin_email, "password": config.sub2api_admin_password},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()["data"]
    _jwt_token = data["access_token"]
    _jwt_expires_at = time.time() + data.get("expires_in", 3600)
    return _jwt_token


async def _fetch_sub2api(client: httpx.AsyncClient) -> dict | None:
    if not config.sub2api_base_url:
        return None
    try:
        global _jwt_token, _jwt_expires_at
        token = await _retry(lambda: _sub2api_login(client))

        async def _get_stats():
            nonlocal token
            resp = await client.get(
                f"{config.sub2api_base_url}/api/v1/admin/dashboard/stats",
                headers={"Authorization": f"Bearer {token}"},
                timeout=15,
            )
            if resp.status_code == 401:
                _jwt_token_ref = None
                token = await _retry(lambda: _sub2api_login(client))
                resp = await client.get(
                    f"{config.sub2api_base_url}/api/v1/admin/dashboard/stats",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=15,
                )
            resp.raise_for_status()
            return resp.json()["data"]

        async def _get_usage_stats():
            """Fetch accounts and aggregate 7d usage percent from extra fields."""
            sum_7d = 0.0
            count_7d = 0
            page = 1
            while True:
                resp = await client.get(
                    f"{config.sub2api_base_url}/api/v1/admin/accounts",
                    headers={"Authorization": f"Bearer {token}"},
                    params={"page": page, "page_size": 100},
                    timeout=15,
                )
                resp.raise_for_status()
                body = resp.json()
                paged = body.get("data", {})
                items = paged.get("items", []) if isinstance(paged, dict) else []
                for acc in items:
                    extra = acc.get("extra") or {}
                    pct_7d = extra.get("codex_7d_used_percent")
                    if pct_7d is not None:
                        sum_7d += float(pct_7d)
                        count_7d += 1
                total_count = paged.get("total", 0) if isinstance(paged, dict) else 0
                if page * 100 >= total_count:
                    break
                page += 1
            avg = sum_7d / count_7d if count_7d else 0
            return {"usage_7d_avg": avg, "usage_7d_count": count_7d}

        stats, usage_pct = await asyncio.gather(
            _retry(_get_stats),
            _retry(_get_usage_stats),
        )
        normal = int(stats.get("normal_accounts") or 0)
        ratelimit = int(stats.get("ratelimit_accounts") or 0)
        overload = int(stats.get("overload_accounts") or 0)
        return {
            "name": "Sub2API",
            "total": int(stats.get("total_accounts") or 0),
            "available": normal - ratelimit - overload,
            "error": int(stats.get("error_accounts") or 0),
            "today_requests": int(stats.get("today_requests") or 0),
            "today_tokens": int(stats.get("today_tokens") or 0),
            "total_requests": int(stats.get("total_requests") or 0),
            "total_tokens": int(stats.get("total_tokens") or 0),
            "today_cost": float(stats.get("today_cost") or 0),
            "total_cost": float(stats.get("total_cost") or 0),
            "rpm": float(stats.get("rpm") or 0),
            "tpm": float(stats.get("tpm") or 0),
            "usage_7d_avg": usage_pct.get("usage_7d_avg", 0),
            "status": "online",
        }
    except Exception as e:
        logger.warning("Sub2API fetch failed: %s", e)
        return {"name": "Sub2API", "status": "offline", "error_msg": str(e)}


# ── CPA ──────────────────────────────────────────────

async def _fetch_cpa(client: httpx.AsyncClient) -> dict | None:
    if not config.cpa_base_url:
        return None
    headers = {"Authorization": f"Bearer {config.cpa_management_key}"}
    try:
        async def _get(path):
            resp = await client.get(f"{config.cpa_base_url}{path}", headers=headers, timeout=15)
            resp.raise_for_status()
            return resp.json()

        usage_data, auth_data = await asyncio.gather(
            _retry(lambda: _get("/v0/management/usage")),
            _retry(lambda: _get("/v0/management/auth-files")),
        )
        usage = usage_data.get("usage", {})
        files = auth_data.get("files", [])
        today_key = datetime.now(CST).strftime("%Y-%m-%d")
        return {
            "name": "CPA",
            "total": len(files),
            "available": sum(1 for f in files if f.get("status") == "active" and not f.get("disabled")),
            "error": sum(1 for f in files if f.get("status") == "error"),
            "today_requests": (usage.get("requests_by_day") or {}).get(today_key, 0),
            "today_tokens": (usage.get("tokens_by_day") or {}).get(today_key, 0),
            "total_requests": int(usage.get("total_requests") or 0),
            "total_tokens": int(usage.get("total_tokens") or 0),
            "today_cost": 0,
            "total_cost": 0,
            "rpm": 0,
            "tpm": 0,
            "status": "online",
        }
    except Exception as e:
        logger.warning("CPA fetch failed: %s", e)
        return {"name": "CPA", "status": "offline", "error_msg": str(e)}


# ── Codex2API ────────────────────────────────────────

async def _fetch_codex(client: httpx.AsyncClient) -> dict | None:
    if not config.codex2api_base_url:
        return None
    headers = {"X-Admin-Key": config.codex2api_admin_key}
    try:
        async def _get(path):
            resp = await client.get(
                f"{config.codex2api_base_url}/api/admin{path}", headers=headers, timeout=15,
            )
            resp.raise_for_status()
            return resp.json()

        ops, accounts_resp = await asyncio.gather(
            _retry(lambda: _get("/ops/overview")),
            _retry(lambda: _get("/accounts")),
        )
        accounts = accounts_resp if isinstance(accounts_resp, list) else accounts_resp.get("accounts", [])
        traffic = ops.get("traffic", {})
        # Aggregate 7d usage percent from accounts
        sum_7d = 0.0
        count_7d = 0
        for a in accounts:
            pct = a.get("usage_percent_7d")
            if pct is not None:
                sum_7d += float(pct)
                count_7d += 1
        return {
            "name": "Codex2API",
            "total": len(accounts),
            "available": sum(1 for a in accounts if a.get("status") == "active" and not a.get("locked")),
            "error": sum(1 for a in accounts if a.get("status") not in ("active",) and not a.get("locked")),
            "today_requests": int(traffic.get("today_requests") or 0),
            "today_tokens": int(traffic.get("today_tokens") or 0),
            "total_requests": int(ops.get("requests", {}).get("total") or 0),
            "total_tokens": 0,
            "today_cost": 0,
            "total_cost": 0,
            "rpm": float(traffic.get("rpm") or 0),
            "tpm": float(traffic.get("tpm") or 0),
            "usage_7d_avg": sum_7d / count_7d if count_7d else 0,
            "status": "online",
        }
    except Exception as e:
        logger.warning("Codex2API fetch failed: %s", e)
        return {"name": "Codex2API", "status": "offline", "error_msg": str(e)}


# ── Handler ──────────────────────────────────────────

ai_status_cmd = on_fullmatch(("AI中转状态", "ai中转状态"))


@ai_status_cmd.handle()
async def _():
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            _fetch_sub2api(client),
            _fetch_cpa(client),
            _fetch_codex(client),
        )

    services = [r for r in results if r is not None]
    if not services:
        await ai_status_cmd.finish("未配置任何AI服务")

    # Aggregate
    online = [s for s in services if s.get("status") == "online"]
    svcs_with_7d = [s for s in online if s.get("usage_7d_avg")]
    total_acct = sum(s.get("total", 0) for s in online)
    avail_acct = sum(s.get("available", 0) for s in online)
    stats = {
        "services": services,
        "total_accounts": total_acct,
        "available_accounts": avail_acct,
        "unavailable_accounts": total_acct - avail_acct,
        "today_requests": sum(s.get("today_requests", 0) for s in online),
        "today_tokens": sum(s.get("today_tokens", 0) for s in online),
        "total_requests": sum(s.get("total_requests", 0) for s in online),
        "total_tokens": sum(s.get("total_tokens", 0) for s in online),
        "today_cost": sum(s.get("today_cost", 0) for s in online),
        "total_cost": sum(s.get("total_cost", 0) for s in online),
        "total_rpm": sum(s.get("rpm", 0) for s in online),
        "total_tpm": sum(s.get("tpm", 0) for s in online),
        "usage_7d_avg": sum(s["usage_7d_avg"] for s in svcs_with_7d) / len(svcs_with_7d) if svcs_with_7d else 0,
        "online_count": len(online),
        "total_count": len(services),
        "updated_at": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S"),
    }

    image_bytes = render_status_card(stats)
    await ai_status_cmd.finish(await UniMsg.image(raw=image_bytes).export())
