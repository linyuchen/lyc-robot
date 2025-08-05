from nonebot.plugin.on import on_command
from nonebot_plugin_alconna import UniMsg

from src.common.ai_chat.yuanbao.login import TXYuanBaoLogin
from src.common.config import CONFIG

login_cmd = on_command('登录元宝')


@login_cmd.handle()
async def login_yuanbao_cmd():
    yuanbao_login = TXYuanBaoLogin()
    try:
        await yuanbao_login.init()
        qrcode_path = await yuanbao_login.get_qrcode()
        msg = UniMsg.image(raw=qrcode_path.read_bytes()) + UniMsg.text("请用 QQ 扫码登录")
        await login_cmd.send(await msg.export())
        qrcode_path.unlink()
    except TimeoutError as e:
        await yuanbao_login.close()
        await login_cmd.finish('获取二维码超时')

    try:
        cookie = await yuanbao_login.get_cookie()
        for chat_config in CONFIG.ai_chats:
            if '元宝' in chat_config.model:
                chat_config.api_key = f'{cookie["hy_user"]} {cookie["hy_token"]} {cookie["client_id"]}'
    except TimeoutError as e:
        await yuanbao_login.close()
        await login_cmd.finish('登录超时')
    await yuanbao_login.close()
    await login_cmd.finish('登录成功')