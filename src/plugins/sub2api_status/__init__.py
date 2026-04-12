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


sub2api_status_cmd = on_fullmatch("sub2api状态", permission=SUPERUSER)


@sub2api_status_cmd.handle()
async def _():
    if not config.sub2api_base_url:
        await sub2api_status_cmd.finish("未配置 SUB2API_BASE_URL")

    try:
        stats = await fetch_dashboard_stats()
    except httpx.HTTPStatusError as e:
        await sub2api_status_cmd.finish(f"API请求失败: HTTP {e.response.status_code}")
    except Exception as e:
        await sub2api_status_cmd.finish(f"获取状态失败: {e}")

    image_bytes = render_status_card(stats)
    await sub2api_status_cmd.finish(await UniMsg.image(raw=image_bytes).export())
