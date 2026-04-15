import asyncio
import time

import httpx
from nonebot import get_plugin_config, on_fullmatch
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from nonebot_plugin_alconna import UniMsg
from pydantic import BaseModel

from .render import render_status_card

__plugin_meta__ = PluginMetadata(
    name="Sub2API状态",
    description="查看Sub2API服务状态和统计信息",
    usage="sub2api状态（仅主人可用）",
)


class Sub2ApiConfig(BaseModel):
    sub2api_base_url: str = ""
    sub2api_admin_email: str = ""
    sub2api_admin_password: str = ""


config = get_plugin_config(Sub2ApiConfig)

# JWT token cache
_jwt_token: str | None = None
_jwt_expires_at: float = 0

MAX_RETRIES = 3


async def get_jwt_token() -> str:
    global _jwt_token, _jwt_expires_at

    if _jwt_token and time.time() < _jwt_expires_at - 60:
        return _jwt_token

    last_err = None
    for i in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{config.sub2api_base_url}/api/v1/auth/login",
                    json={
                        "email": config.sub2api_admin_email,
                        "password": config.sub2api_admin_password,
                    },
                    timeout=10,
                )
                resp.raise_for_status()
                data = resp.json()["data"]
                _jwt_token = data["access_token"]
                expires_in = data.get("expires_in", 3600)
                _jwt_expires_at = time.time() + expires_in
                return _jwt_token
        except Exception as e:
            last_err = e
            if i < MAX_RETRIES - 1:
                await asyncio.sleep(1)
    raise last_err


async def fetch_dashboard_stats() -> dict:
    global _jwt_token, _jwt_expires_at

    token = await get_jwt_token()
    last_err = None
    for i in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{config.sub2api_base_url}/api/v1/admin/dashboard/stats",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=15,
                )
                # Token expired, refresh and retry
                if resp.status_code == 401:
                    _jwt_token = None
                    _jwt_expires_at = 0
                    token = await get_jwt_token()
                    continue
                resp.raise_for_status()
                return resp.json()["data"]
        except Exception as e:
            last_err = e
            if i < MAX_RETRIES - 1:
                await asyncio.sleep(1)
    raise last_err


async def fetch_accounts_usage_7d() -> dict:
    """Fetch accounts list and aggregate 7d usage percent from extra fields."""
    global _jwt_token, _jwt_expires_at

    token = await get_jwt_token()
    sum_7d = 0.0
    count_7d = 0

    page = 1
    page_size = 100
    while True:
        last_err = None
        for i in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        f"{config.sub2api_base_url}/api/v1/admin/accounts",
                        headers={"Authorization": f"Bearer {token}"},
                        params={"page": page, "page_size": page_size},
                        timeout=15,
                    )
                    if resp.status_code == 401:
                        _jwt_token = None
                        _jwt_expires_at = 0
                        token = await get_jwt_token()
                        continue
                    resp.raise_for_status()
                    body = resp.json()
                    paged = body.get("data", {})
                    items = paged.get("items", []) if isinstance(paged, dict) else []
                    for acc in items:
                        extra = acc.get("extra") or {}
                        pct = extra.get("codex_7d_used_percent")
                        if pct is not None:
                            sum_7d += float(pct)
                            count_7d += 1
                    total_count = paged.get("total", 0) if isinstance(paged, dict) else 0
                    last_err = None
                    break
            except Exception as e:
                last_err = e
                if i < MAX_RETRIES - 1:
                    await asyncio.sleep(1)
        if last_err:
            break
        if page * page_size >= total_count:
            break
        page += 1

    avg = sum_7d / count_7d if count_7d else 0
    return {"usage_7d_avg": avg, "usage_7d_count": count_7d}


sub2api_status_cmd = on_fullmatch("sub2api状态", permission=SUPERUSER)


@sub2api_status_cmd.handle()
async def _():
    if not config.sub2api_base_url:
        await sub2api_status_cmd.finish("未配置 SUB2API_BASE_URL")

    try:
        stats, usage_7d = await asyncio.gather(
            fetch_dashboard_stats(),
            fetch_accounts_usage_7d(),
        )
        stats.update(usage_7d)
    except httpx.HTTPStatusError as e:
        await sub2api_status_cmd.finish(f"API请求失败: HTTP {e.response.status_code}")
    except Exception as e:
        await sub2api_status_cmd.finish(f"获取状态失败: {e}")

    image_bytes = render_status_card(stats)
    await sub2api_status_cmd.finish(await UniMsg.image(raw=image_bytes).export())
